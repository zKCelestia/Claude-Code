"""Bot Telegram yang meneruskan chat ke Claude Managed Agent.

Setiap chat Telegram mendapat satu session sendiri, jadi agent ingat percakapan
sebelumnya. Perintah:
  /start  - sapaan
  /reset  - mulai percakapan baru (session baru)

Pengguna juga bisa mengirim file/foto; file hasil buatan agent (Excel, Word,
PowerPoint, PDF, dll.) di /mnt/session/outputs/ dikirim balik sebagai dokumen.

Jalankan setelah setup_agent.py:  python bot.py
"""

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "agent_config.json"
SESSIONS_PATH = BASE_DIR / "sessions.json"
TELEGRAM_LIMIT = 4000  # batas Telegram 4096 karakter per pesan
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # bot Telegram hanya bisa mengunduh file <= 20 MB
MAX_SEND_BYTES = 50 * 1024 * 1024  # bot Telegram hanya bisa mengirim file <= 50 MB

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

load_dotenv()
client = anthropic.Anthropic()

if not CONFIG_PATH.exists():
    raise SystemExit("agent_config.json belum ada. Jalankan dulu: python setup_agent.py")
CONFIG = json.loads(CONFIG_PATH.read_text())

ALLOWED_USER_IDS = {
    int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x
}

# chat_id -> {"session_id": ..., "sent_files": [file_id, ...]}
sessions: dict[str, dict] = json.loads(SESSIONS_PATH.read_text()) if SESSIONS_PATH.exists() else {}
for _k, _v in list(sessions.items()):  # format lama: chat_id -> session_id
    if isinstance(_v, str):
        sessions[_k] = {"session_id": _v, "sent_files": []}
chat_locks: dict[int, asyncio.Lock] = {}


def save_sessions() -> None:
    SESSIONS_PATH.write_text(json.dumps(sessions, indent=2))


def get_or_create_session(chat_id: int) -> str:
    key = str(chat_id)
    if key not in sessions:
        session = client.beta.sessions.create(
            agent=CONFIG["agent_id"],  # selalu versi agent terbaru
            environment_id=CONFIG["environment_id"],
            title=f"Telegram chat {chat_id}",
        )
        sessions[key] = {"session_id": session.id, "sent_files": []}
        save_sessions()
        log.info("Session baru %s untuk chat %s", session.id, chat_id)
    return sessions[key]["session_id"]


def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w.\-]+", "_", Path(name).name).strip("._")
    return name or "file"


def attach_file(session_id: str, data: bytes, filename: str) -> str:
    """Unggah file ke Files API, pasang ke session, dan kembalikan path-nya di sandbox."""
    filename = safe_filename(filename)
    uploaded = client.beta.files.upload(file=(filename, data))
    mount = f"/{uploaded.id}/{filename}"  # folder per file supaya nama tidak bentrok
    client.beta.sessions.resources.add(
        session_id=session_id, type="file", file_id=uploaded.id, mount_path=mount
    )
    return f"/mnt/session/uploads{mount}"


def collect_new_outputs(chat_id: int, session_id: str, expect_files: bool) -> list[tuple[str, bytes]]:
    """Unduh file baru di /mnt/session/outputs/ yang belum pernah dikirim ke chat ini."""
    state = sessions[str(chat_id)]
    sent = set(state["sent_files"])
    new_files = []
    attempts = 4 if expect_files else 1  # file outputs muncul ~1-3 detik setelah session idle
    for attempt in range(attempts):
        new_files = [
            f
            for f in client.beta.files.list(scope_id=session_id, betas=["managed-agents-2026-04-01"])
            if f.id not in sent
        ]
        if new_files or attempt == attempts - 1:
            break
        time.sleep(1.5)

    results = []
    for f in new_files:
        state["sent_files"].append(f.id)
        if f.size_bytes and f.size_bytes > MAX_SEND_BYTES:
            log.warning("File %s terlalu besar untuk Telegram (%s byte)", f.filename, f.size_bytes)
            continue
        results.append((f.filename, client.beta.files.download(f.id).read()))
    save_sessions()
    return results


def run_turn(session_id: str, text: str) -> tuple[str, bool]:
    """Kirim satu pesan ke session lalu kumpulkan balasan agent sampai session idle.

    Berjalan sinkron; dipanggil lewat asyncio.to_thread agar bot tetap responsif.
    Mengembalikan (teks balasan, apakah agent menyentuh /mnt/session/outputs/).
    """
    parts: list[str] = []
    touched_outputs = False
    # Stream-first: buka stream dulu, baru kirim pesan.
    with client.beta.sessions.events.stream(session_id=session_id) as stream:
        client.beta.sessions.events.send(
            session_id=session_id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if block.type == "text":
                        parts.append(block.text)
            if event.type == "agent.tool_use" and "/mnt/session/outputs" in json.dumps(
                getattr(event, "input", None), default=str
            ):
                touched_outputs = True
            if event.type in ("agent.tool_use", "agent.mcp_tool_use") and getattr(
                event, "evaluated_permission", None
            ) == "ask":
                # Tidak ada orang yang menyetujui aksi berisiko dari Telegram: tolak.
                client.beta.sessions.events.send(
                    session_id=session_id,
                    events=[
                        {"type": "user.tool_confirmation", "tool_use_id": event.id, "result": "deny"}
                    ],
                )
            elif event.type == "session.status_idle":
                if event.stop_reason.type != "requires_action":
                    break
            elif event.type == "session.status_terminated":
                raise SessionGone()
    reply = "\n\n".join(p.strip() for p in parts if p.strip()) or "(Agent tidak memberi jawaban teks.)"
    return reply, touched_outputs


class SessionGone(Exception):
    pass


def split_message(text: str) -> list[str]:
    chunks = []
    while len(text) > TELEGRAM_LIMIT:
        cut = text.rfind("\n", 0, TELEGRAM_LIMIT)
        if cut <= 0:
            cut = TELEGRAM_LIMIT
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    chunks.append(text)
    return chunks


def is_allowed(update: Update) -> bool:
    return not ALLOWED_USER_IDS or (
        update.effective_user is not None and update.effective_user.id in ALLOWED_USER_IDS
    )


async def keep_typing(chat, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await chat.send_action(ChatAction.TYPING)
        except Exception:  # indikator mengetik tidak penting
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=4)
        except asyncio.TimeoutError:
            pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "Halo! Saya asisten AI. Kirim pertanyaan apa saja, atau kirim file "
        "(Excel, Word, PDF, foto) untuk dibaca dan diolah. Saya juga bisa membuatkan "
        "file Excel, Word, PowerPoint dan PDF.\n/reset untuk mulai percakapan baru."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    sessions.pop(str(update.effective_chat.id), None)
    save_sessions()
    await update.message.reply_text("Percakapan direset. Silakan mulai topik baru.")


async def build_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: str) -> str:
    """Teks pesan untuk agent; file/foto dari Telegram dipasang ke session dulu."""
    msg = update.message
    text = msg.text or msg.caption or ""
    tg_file, filename = None, None
    if msg.document:
        tg_file, filename = msg.document, msg.document.file_name or "dokumen"
    elif msg.photo:
        tg_file, filename = msg.photo[-1], f"foto_{msg.message_id}.jpg"  # resolusi terbesar
    if tg_file is None:
        return text

    if tg_file.file_size and tg_file.file_size > MAX_UPLOAD_BYTES:
        raise UserFacingError("File terlalu besar. Bot Telegram hanya bisa menerima file sampai 20 MB.")
    data = bytes(await (await context.bot.get_file(tg_file.file_id)).download_as_bytearray())
    path = await asyncio.to_thread(attach_file, session_id, data, filename)
    instruction = text or "Lihat file ini dan beri tahu saya isinya secara singkat."
    return f"[Pengguna mengirim file: {path}]\n\n{instruction}"


class UserFacingError(Exception):
    pass


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await update.message.reply_text("Maaf, kamu tidak punya akses ke bot ini.")
        return

    chat_id = update.effective_chat.id
    lock = chat_locks.setdefault(chat_id, asyncio.Lock())
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(update.effective_chat, stop_typing))
    outputs: list[tuple[str, bytes]] = []

    try:
        async with lock:  # satu giliran per chat pada satu waktu
            for attempt in range(2):
                session_id = await asyncio.to_thread(get_or_create_session, chat_id)
                try:
                    prompt = await build_prompt(update, context, session_id)
                    reply, wrote_outputs = await asyncio.to_thread(run_turn, session_id, prompt)
                    break
                except (SessionGone, anthropic.NotFoundError):
                    log.warning("Session %s tidak bisa dipakai, membuat yang baru", session_id)
                    sessions.pop(str(chat_id), None)
                    save_sessions()
                    if attempt == 1:
                        raise
            try:
                outputs = await asyncio.to_thread(
                    collect_new_outputs, chat_id, session_id, wrote_outputs
                )
            except anthropic.APIError:
                log.exception("Gagal mengambil file hasil agent")
                reply += "\n\n(File hasil tidak bisa diambil. Coba minta lagi.)"
    except UserFacingError as e:
        reply = str(e)
    except anthropic.RateLimitError:
        reply = "Server sedang sibuk (rate limit). Coba lagi sebentar lagi ya."
    except anthropic.APIStatusError as e:
        log.exception("API error")
        reply = f"Maaf, terjadi kesalahan dari API ({e.status_code})."
    except anthropic.APIConnectionError:
        log.exception("Koneksi gagal")
        reply = "Maaf, koneksi ke server AI gagal. Coba lagi."
    except Exception:
        log.exception("Error tak terduga")
        reply = "Maaf, terjadi kesalahan. Coba lagi atau ketik /reset."
    finally:
        stop_typing.set()
        await typing_task

    for chunk in split_message(reply):
        await update.message.reply_text(chunk)
    for filename, data in outputs:
        await update.message.reply_document(document=data, filename=filename)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN belum diisi di file .env")

    app = Application.builder().token(token).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) | filters.Document.ALL | filters.PHOTO, handle_message
        )
    )
    log.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
