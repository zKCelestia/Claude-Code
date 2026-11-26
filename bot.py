"""Bot Telegram yang meneruskan chat ke Claude Managed Agent.

Setiap chat Telegram mendapat satu session sendiri, jadi agent ingat percakapan
sebelumnya. Perintah:
  /start  - sapaan
  /reset  - mulai percakapan baru (session baru)

Pengguna juga bisa mengirim file/foto; file hasil buatan agent (Excel, Word,
PowerPoint, PDF, dll.) di /mnt/session/outputs/ dikirim balik sebagai dokumen.

Burner wallet (opsional, lihat burner/):
  /wallet  - alamat, saldo, dan sisa budget
  /stop    - pause semua transaksi burner (kill switch)
  /resume  - aktifkan lagi

Mode grup (lihat group_chat.py): ngobrol bareng bot lain (mis. Muse) di grup
yang ID-nya ada di GROUP_CHAT_IDS.
  /status  - siapa terakhir ngomong, siapa yang nggak aktif
  /jewer   - mention anggota yang nggak aktif (pemilik saja)

Pemantau airdrop (lihat monitor/):
  /pantau                    - daftar yang dipantau
  /pantau tg <channel>       - tambah channel Telegram publik
  /pantau x <akun>           - tambah akun X (butuh X_BEARER_TOKEN)
  /lepas tg|x <nama>         - berhenti memantau
  /kunci <kata> | /kunci     - tambah kata kunci / lihat daftar
  /cekairdrop                - cek sekarang

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
from telegram.error import Conflict
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from group_chat import GroupManager, GroupSettings, Incoming
from monitor import watcher

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

GROUP_CHAT_IDS = {
    int(x) for x in os.environ.get("GROUP_CHAT_IDS", "").replace(" ", "").split(",") if x
}
WATCHDOG_INTERVAL = 300  # detik
WATCHDOG_MAX_FAILS = 3

# ---------- burner wallet (opsional) ----------
burner = None
BURNER_STATUS = "Burner wallet belum disiapkan (lihat README bagian Burner wallet)."
try:
    from burner.tools import Burner

    burner = Burner()
    if not ALLOWED_USER_IDS:
        burner = None
        BURNER_STATUS = (
            "Burner dinonaktifkan: isi ALLOWED_USER_IDS di .env dulu, supaya orang lain "
            "tidak bisa memakai saldo burner lewat bot."
        )
        log.warning(BURNER_STATUS)
    else:
        BURNER_STATUS = "aktif"
        log.info("Burner wallet aktif (EVM: %s, Solana: %s)", burner.evm and burner.evm.address, burner.sol and burner.sol.address)
except Exception as e:  # policy/.env.burner belum ada atau library belum terinstal
    BURNER_STATUS = f"Burner tidak aktif: {e}"
    log.info(BURNER_STATUS)


def run_custom_tool(name: str, args: dict, allow_burner: bool = True) -> tuple[str, dict | None]:
    if name.startswith("burner_"):
        if not allow_burner and name != "burner_status":
            reason = (
                "Transaksi burner hanya boleh atas perintah langsung pemilik. Giliran ini dipicu "
                "pesan grup/bot lain, jadi tidak dijalankan."
            )
            return f"DITOLAK: {reason}", {"rejected": True, "tool": name, "reason": reason}
        if burner is None:
            return f"Burner wallet tidak tersedia. {BURNER_STATUS}", None
        return burner.run_tool(name, args)
    return f"Tool tidak dikenal: {name}", None


def format_tx(tx: dict) -> str:
    if tx.get("rejected"):
        return f"🛑 Burner menolak transaksi ({tx['tool']}):\n{tx['reason']}"
    ref = tx.get("tx_hash") or tx.get("signature")
    lines = [
        f"🔥 Burner tx [{tx.get('chain')}]: {tx.get('status')}",
        f"Biaya: {tx.get('cost')}",
    ]
    if tx.get("to"):
        lines.append(f"Ke: {tx['to']} ({tx.get('to_label', '')})")
    if tx.get("reason"):
        lines.append(f"Alasan: {tx['reason']}")
    lines.append(f"Ref: {ref}")
    return "\n".join(lines)


# chat_id -> {"session_id": ..., "sent_files": [file_id, ...]}
sessions: dict[str, dict] = json.loads(SESSIONS_PATH.read_text()) if SESSIONS_PATH.exists() else {}
for _k, _v in list(sessions.items()):  # format lama: chat_id -> session_id
    if isinstance(_v, str):
        sessions[_k] = {"session_id": _v, "sent_files": []}
chat_locks: dict[int, asyncio.Lock] = {}


def save_sessions() -> None:
    SESSIONS_PATH.write_text(json.dumps(sessions, indent=2))


def get_or_create_session(chat_id: int | str) -> str:
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


def run_turn(session_id: str, text: str, allow_burner: bool = True) -> tuple[str, bool, list[dict]]:
    """Kirim satu pesan ke session lalu kumpulkan balasan agent sampai session idle.

    Berjalan sinkron; dipanggil lewat asyncio.to_thread agar bot tetap responsif.
    Mengembalikan (teks balasan, apakah agent menyentuh /mnt/session/outputs/,
    daftar transaksi burner yang terjadi).
    """
    parts: list[str] = []
    touched_outputs = False
    txs: list[dict] = []
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
            if event.type == "agent.custom_tool_use":
                result_text, tx = run_custom_tool(event.name, dict(event.input or {}), allow_burner)
                if tx:
                    txs.append(tx)
                client.beta.sessions.events.send(
                    session_id=session_id,
                    events=[
                        {
                            "type": "user.custom_tool_result",
                            "custom_tool_use_id": event.id,
                            "content": [{"type": "text", "text": result_text}],
                        }
                    ],
                )
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
    return reply, touched_outputs, txs


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
    txs: list[dict] = []

    try:
        async with lock:  # satu giliran per chat pada satu waktu
            for attempt in range(2):
                session_id = await asyncio.to_thread(get_or_create_session, chat_id)
                try:
                    prompt = await build_prompt(update, context, session_id)
                    reply, wrote_outputs, txs = await asyncio.to_thread(run_turn, session_id, prompt)
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

    for tx in txs:
        await update.message.reply_text(format_tx(tx))
    for chunk in split_message(reply):
        await update.message.reply_text(chunk)
    for filename, data in outputs:
        await update.message.reply_document(document=data, filename=filename)


async def wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    if burner is None:
        await update.message.reply_text(BURNER_STATUS)
        return
    status = await asyncio.to_thread(burner.status)
    lines = ["⏸ PAUSED" if status["paused"] else "▶️ Aktif"]
    if status.get("evm_address"):
        lines.append(f"\nEVM: {status['evm_address']}")
        for name, c in status["evm"].items():
            lines.append(f"  {name}: {c['saldo']} | sisa hari ini {c['sisa_hari_ini']}")
    if status.get("solana"):
        c = status["solana"]
        lines.append(f"\nSolana: {c['address']}")
        lines.append(f"  {c['saldo']} | sisa hari ini {c['sisa_hari_ini']}")
    await update.message.reply_text("\n".join(lines))


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    if burner is None:
        await update.message.reply_text(BURNER_STATUS)
        return
    burner.guard.set_paused(True)
    await update.message.reply_text("⏸ Burner di-pause. Semua transaksi ditolak sampai /resume.")


async def resume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    if burner is None:
        await update.message.reply_text(BURNER_STATUS)
        return
    burner.guard.set_paused(False)
    await update.message.reply_text("▶️ Burner aktif lagi (tetap dalam batas policy).")


async def autopilot_loop(app: Application) -> None:
    """Jalankan tugas garapan berkala tanpa disuruh, lalu laporkan ke pemilik."""
    await asyncio.sleep(60)
    while True:
        interval = 6.0
        try:
            if burner is not None:
                burner.guard.reload()
                cfg = burner.guard.policy.get("autopilot") or {}
                interval = float(cfg.get("interval_hours", 6))
                if cfg.get("enabled") and not burner.guard.paused:
                    await run_autopilot_once(app, cfg["prompt"])
        except Exception:
            log.exception("Autopilot error")
        await asyncio.sleep(max(0.25, interval) * 3600)


async def run_autopilot_once(app: Application, prompt: str) -> None:
    lock = chat_locks.setdefault("autopilot", asyncio.Lock())
    async with lock:
        session_id = await asyncio.to_thread(get_or_create_session, "autopilot")
        log.info("Autopilot jalan (session %s)", session_id)
        try:
            reply, _, txs = await asyncio.to_thread(run_turn, session_id, "[AUTOPILOT]\n" + prompt)
        except SessionGone:
            sessions.pop("autopilot", None)
            save_sessions()
            return
    report = ["🤖 Laporan autopilot"] + [format_tx(tx) for tx in txs] + [reply]
    for owner in ALLOWED_USER_IDS:
        for chunk in split_message("\n\n".join(report)):
            try:
                await app.bot.send_message(chat_id=owner, text=chunk)
            except Exception:
                log.exception("Gagal kirim laporan autopilot ke %s", owner)


# ---------------------------------------------------------------- mode grup
groups: GroupManager | None = None


async def group_turn(chat_id: int, prompt: str, allow_burner: bool) -> tuple[str, list[dict]]:
    lock = chat_locks.setdefault(chat_id, asyncio.Lock())
    async with lock:
        for attempt in range(2):
            session_id = await asyncio.to_thread(get_or_create_session, chat_id)
            try:
                reply, _, txs = await asyncio.to_thread(run_turn, session_id, prompt, allow_burner)
                return reply, txs
            except (SessionGone, anthropic.NotFoundError):
                sessions.pop(str(chat_id), None)
                save_sessions()
                if attempt == 1:
                    raise
    return "", []


def is_addressed(msg, me_id: int | None, me_username: str | None) -> bool:
    text = (msg.text or "").lower()
    if me_username and f"@{me_username.lower()}" in text:
        return True
    reply = msg.reply_to_message
    return bool(reply and reply.from_user and reply.from_user.id == me_id)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    if groups is None or not msg or not msg.text or not msg.from_user:
        return
    if chat.id not in GROUP_CHAT_IDS:
        return
    user = msg.from_user
    groups.receive(
        chat.id,
        chat.title or "",
        Incoming(
            user_id=user.id,
            name=user.full_name or user.username or str(user.id),
            username=user.username,
            is_bot=bool(user.is_bot),
            is_owner=user.id in ALLOWED_USER_IDS,
            addressed=is_addressed(msg, groups.me_id, groups.me_username),
            text=msg.text,
        ),
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if groups is None or chat.id not in GROUP_CHAT_IDS:
        if is_allowed(update):
            await update.effective_message.reply_text(
                f"Mode grup belum aktif di chat ini. ID chat ini: {chat.id}\n"
                "Tambahkan ke GROUP_CHAT_IDS di .env lalu restart bot."
            )
        return
    await update.effective_message.reply_text(groups.status_text(chat.id))


async def jewer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if groups is None or chat.id not in GROUP_CHAT_IDS or not is_allowed(update):
        return
    names = groups.inactive_mentions(chat.id)
    if not names:
        await update.effective_message.reply_text("Semua masih aktif, nggak ada yang perlu dijewer 👍")
        return
    await update.effective_message.reply_text(
        " ".join(names) + " 👋 kalian ke mana? Ayo ikut ngobrol lagi, kasih update terbaru kalian."
    )


# ---------------------------------------------------------------- watchdog
async def watchdog_loop(app: Application) -> None:
    """Cek koneksi ke Telegram secara berkala, bukan cuma 'proses masih hidup'.

    Kalau gagal berkali-kali berturut-turut, proses keluar dengan kode 1 supaya
    systemd/pm2/docker me-restart bot.
    """
    fails = 0
    while True:
        await asyncio.sleep(WATCHDOG_INTERVAL)
        try:
            await app.bot.get_me()
            fails = 0
        except Exception as e:
            fails += 1
            log.warning("Watchdog: cek Telegram gagal (%s/%s): %s", fails, WATCHDOG_MAX_FAILS, e)
            if fails >= WATCHDOG_MAX_FAILS:
                log.error("Watchdog: Telegram tidak bisa dijangkau. Keluar supaya di-restart.")
                os._exit(1)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        log.error(
            "409 Conflict: token bot ini sedang dipakai proses lain (getUpdates). "
            "Telegram cuma izinkan 1 poller per bot. Matikan proses lain atau pakai token berbeda."
        )
        return
    log.error("Error saat memproses update", exc_info=context.error)


# ---------------------------------------------------------------- pemantau airdrop
monitor_lock = asyncio.Lock()


async def run_monitor_once(app: Application, notify_empty_to: int | None = None) -> None:
    async with monitor_lock:
        alerts, errors = await asyncio.to_thread(watcher.check_once)
    for err in errors:
        log.warning("Monitor: %s", err)
    targets = [notify_empty_to] if notify_empty_to else sorted(ALLOWED_USER_IDS)
    for owner in targets:
        for a in alerts:
            try:
                await app.bot.send_message(chat_id=owner, text=watcher.format_alert(a), disable_web_page_preview=True)
            except Exception:
                log.exception("Gagal kirim alert ke %s", owner)
        if notify_empty_to and not alerts:
            msg = "Nggak ada postingan airdrop baru."
            if errors:
                msg += "\nMasalah: " + "; ".join(errors[:5])
            await app.bot.send_message(chat_id=owner, text=msg)


async def monitor_loop(app: Application) -> None:
    await asyncio.sleep(30)
    while True:
        interval = 15
        try:
            wl = watcher.load_watchlist()
            interval = max(5, int(wl.get("interval_minutes", 15)))
            if (wl["telegram"] or wl["x"]) and ALLOWED_USER_IDS:
                await run_monitor_once(app)
        except Exception:
            log.exception("Monitor error")
        await asyncio.sleep(interval * 60)


async def pantau_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    wl = watcher.load_watchlist()
    args = context.args
    if len(args) == 2 and args[0].lower() in ("tg", "x"):
        kind = "telegram" if args[0].lower() == "tg" else "x"
        name = args[1].lstrip("@").replace("https://t.me/", "").replace("https://x.com/", "").strip("/")
        if not watcher.valid_name(name):
            await update.message.reply_text("Nama nggak valid. Pakai nama channel/akun tanpa @, contoh: /pantau tg namachannel")
            return
        if name not in wl[kind]:
            wl[kind].append(name)
            watcher.save_watchlist(wl)
        note = ""
        if kind == "x" and not os.environ.get("X_BEARER_TOKEN"):
            note = "\n⚠️ X_BEARER_TOKEN belum diisi di .env, jadi akun X belum dicek."
        await update.message.reply_text(
            f"Oke, {kind} @{name} dipantau. Postingan lama dicatat dulu, alert mulai dari postingan berikutnya.{note}"
        )
        return
    x_status = "aktif" if os.environ.get("X_BEARER_TOKEN") else "nonaktif (isi X_BEARER_TOKEN)"
    tg = ", ".join("@" + n for n in wl["telegram"]) or "-"
    xs = ", ".join("@" + n for n in wl["x"]) or "-"
    await update.message.reply_text(
        f"📡 Pemantau airdrop (tiap {wl['interval_minutes']} menit)\n"
        f"Telegram: {tg}\nX [{x_status}]: {xs}\nKata kunci: {len(wl['keywords'])} (lihat /kunci)\n\n"
        "Tambah: /pantau tg <channel> atau /pantau x <akun>"
    )


async def lepas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    args = context.args
    if len(args) != 2 or args[0].lower() not in ("tg", "x"):
        await update.message.reply_text("Format: /lepas tg <channel> atau /lepas x <akun>")
        return
    kind = "telegram" if args[0].lower() == "tg" else "x"
    name = args[1].lstrip("@")
    wl = watcher.load_watchlist()
    if name in wl[kind]:
        wl[kind].remove(name)
        watcher.save_watchlist(wl)
        await update.message.reply_text(f"{kind} @{name} nggak dipantau lagi.")
    else:
        await update.message.reply_text(f"{kind} @{name} memang nggak ada di daftar.")


async def kunci_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    wl = watcher.load_watchlist()
    word = " ".join(context.args).strip().lower()
    if word:
        if word not in wl["keywords"]:
            wl["keywords"].append(word)
            watcher.save_watchlist(wl)
        await update.message.reply_text(f"Kata kunci '{word}' ditambahkan.")
        return
    await update.message.reply_text("Kata kunci: " + ", ".join(wl["keywords"]))


async def cekairdrop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    await update.message.reply_text("Ngecek sekarang…")
    await run_monitor_once(context.application, notify_empty_to=update.effective_chat.id)


async def post_init(app: Application) -> None:
    global groups
    app.create_task(autopilot_loop(app))
    app.create_task(watchdog_loop(app))
    app.create_task(monitor_loop(app))
    if GROUP_CHAT_IDS:
        me = await app.bot.get_me()

        async def send(chat_id: int, text: str) -> None:
            await app.bot.send_message(chat_id=chat_id, text=text)

        groups = GroupManager(GROUP_CHAT_IDS, ALLOWED_USER_IDS, group_turn, send, format_tx, GroupSettings.from_env())
        groups.me_id, groups.me_username = me.id, me.username
        log.info("Mode grup aktif untuk %s sebagai @%s", sorted(GROUP_CHAT_IDS), me.username)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN belum diisi di file .env")

    app = Application.builder().token(token).concurrent_updates(True).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("wallet", wallet_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("resume", resume_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("jewer", jewer_cmd))
    app.add_handler(CommandHandler("pantau", pantau_cmd))
    app.add_handler(CommandHandler("lepas", lepas_cmd))
    app.add_handler(CommandHandler("kunci", kunci_cmd))
    app.add_handler(CommandHandler("cekairdrop", cekairdrop_cmd))
    # Grup: semua pesan teks (termasuk dari bot lain) masuk inbox grup.
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_group_message))
    # Chat pribadi dengan pemilik: perilaku lama (teks, file, foto).
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & ((filters.TEXT & ~filters.COMMAND) | filters.Document.ALL | filters.PHOTO),
            handle_message,
        )
    )
    app.add_error_handler(on_error)
    log.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
