"""Bot Telegram yang meneruskan chat ke Claude Managed Agent.

Setiap chat Telegram mendapat satu session sendiri, jadi agent ingat percakapan
sebelumnya. Perintah:
  /start  - sapaan
  /reset  - mulai percakapan baru (session baru)

Jalankan setelah setup_agent.py:  python bot.py
"""

import asyncio
import json
import logging
import os
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

sessions: dict[str, str] = json.loads(SESSIONS_PATH.read_text()) if SESSIONS_PATH.exists() else {}
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
        sessions[key] = session.id
        save_sessions()
        log.info("Session baru %s untuk chat %s", session.id, chat_id)
    return sessions[key]


def run_turn(session_id: str, text: str) -> str:
    """Kirim satu pesan ke session lalu kumpulkan balasan agent sampai session idle.

    Berjalan sinkron; dipanggil lewat asyncio.to_thread agar bot tetap responsif.
    """
    parts: list[str] = []
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
            elif event.type in ("agent.tool_use", "agent.mcp_tool_use") and getattr(
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
    return "\n\n".join(p.strip() for p in parts if p.strip()) or "(Agent tidak memberi jawaban teks.)"


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
        "Halo! Saya asisten AI. Kirim pertanyaan apa saja.\n/reset untuk mulai percakapan baru."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    sessions.pop(str(update.effective_chat.id), None)
    save_sessions()
    await update.message.reply_text("Percakapan direset. Silakan mulai topik baru.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await update.message.reply_text("Maaf, kamu tidak punya akses ke bot ini.")
        return

    chat_id = update.effective_chat.id
    lock = chat_locks.setdefault(chat_id, asyncio.Lock())
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(update.effective_chat, stop_typing))

    try:
        async with lock:  # satu giliran per chat pada satu waktu
            for attempt in range(2):
                session_id = await asyncio.to_thread(get_or_create_session, chat_id)
                try:
                    reply = await asyncio.to_thread(run_turn, session_id, update.message.text)
                    break
                except (SessionGone, anthropic.NotFoundError):
                    log.warning("Session %s tidak bisa dipakai, membuat yang baru", session_id)
                    sessions.pop(str(chat_id), None)
                    save_sessions()
                    if attempt == 1:
                        raise
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


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN belum diisi di file .env")

    app = Application.builder().token(token).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
