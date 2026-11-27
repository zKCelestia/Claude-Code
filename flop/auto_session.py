"""Sesi agent FLOP Testnet otomatis: jalan sendiri begitu jalur beli inference dibuka.

Dipanggil dari cron VPS (setelah `agent_http.py claim`). Tiap kali jalan:
1. Cek genesis. Cek indexer offer testnet (`/api/session-offers`). Kalau belum ada, keluar diam-diam.
2. Pilih offer yang layak: bukan miner kita sendiri, model ada di katalog gateway testnet,
   punya endpoint (`venue`) https, minEscrow <= MAX_ESCROW, belum kedaluwarsa, miner aktif dan
   tidak di-blacklist. Urutan: venue terverifikasi, settledCount terbanyak, minEscrow terkecil.
3. Rem: maksimal 1 sesi per 24 jam, total escrow 7 hari <= MAX_7D, saldo final harus
   >= escrow + cadangan fee. Kalau rem kena, tidak bayar apa pun.
4. Jalankan CLI resmi `flop session run` (escrow = MAX_ESCROW, dibayar penuh ke miner kalau settle).
5. Kirim ringkasan ke Telegram bos (TELEGRAM_BOT_TOKEN + ALLOWED_USER_IDS dari .env repo).

    python flop/auto_session.py            # jalan normal (bisa bayar kalau semua syarat terpenuhi)
    python flop/auto_session.py --dry-run  # tunjukkan pilihan tanpa bayar

Password dibaca dari file dan hanya dioper lewat env ke proses CLI. Tidak pernah dicetak.
"""

import json
import os
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_http as ah  # noqa: E402

INDEXER = os.environ.get("FLOP_TESTNET_INDEXER", "https://testnet.flopscan.io")
GATEWAY = "https://gateway.testnet.flop.network"
FLOP_BIN = os.environ.get("FLOP_BIN", str(Path.home() / ".local/share/flop-cli/0.10.3/node_modules/.bin/flop"))
STATE = ah.HOME / "auto_session.json"
REPO_ENV = Path(__file__).resolve().parent.parent / ".env"

BASE = Decimal(10) ** 18
MAX_ESCROW = Decimal("0.01")        # FLOP per sesi
MAX_7D = Decimal("0.05")            # FLOP total escrow per 7 hari
FEE_RESERVE = Decimal("0.5")        # FLOP cadangan untuk fee transaksi
MIN_INTERVAL = 24 * 3600            # detik antar sesi
MAX_TOKENS = 64


def now() -> float:
    return time.time()


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sessions": [], "notified": {}}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(state, f, indent=1)


def venue_url(row: dict) -> str | None:
    v = row.get("venue")
    if isinstance(v, dict):
        v = v.get("url") or v.get("endpoint") or v.get("sessionEndpoint")
    if isinstance(v, str) and v.startswith("https://"):
        return v.rstrip("/")
    return None


def catalog() -> dict[str, str]:
    """model_hash (lowercase) -> slug, dari gateway testnet."""
    try:
        data = requests.get(f"{GATEWAY}/v1/models", headers=ah.UA, timeout=30).json()["data"]
    except Exception:  # noqa: BLE001
        return {}
    return {m["x-flop"]["model_hash"].lower(): m["id"] for m in data if m.get("x-flop", {}).get("model_hash")}


def fetch_offers() -> list[dict] | None:
    try:
        r = requests.get(f"{INDEXER}/api/session-offers", params={"limit": "100"}, headers=ah.UA, timeout=30)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    return r.json().get("data", [])


def choose(rows: list[dict], models: dict[str, str], me: str, block: int) -> tuple[dict | None, str]:
    """Kembalikan (kandidat, alasan kalau tidak ada)."""
    ok = []
    no_venue = 0
    for row in rows:
        o = row.get("offer", {})
        facts = row.get("onChainFacts") or {}
        slug = models.get(str(o.get("modelHash", "")).lower())
        url = venue_url(row)
        try:
            min_escrow = Decimal(str(o["minEscrow"])) / BASE
            expiry = int(o.get("expiry", 0))
        except (KeyError, ValueError, ArithmeticError):
            continue
        if o.get("miner") == me or not slug or facts.get("blacklisted") or facts.get("active") is False:
            continue
        if expiry and expiry <= block:
            continue
        if min_escrow > MAX_ESCROW:
            continue
        if not url:
            no_venue += 1
            continue
        settled = int((facts.get("reliability") or {}).get("settledCount") or 0)
        ok.append({"miner": o["miner"], "model": slug, "endpoint": url, "min_escrow": min_escrow,
                   "verified": bool(row.get("venueVerified")), "settled": settled})
    if not ok:
        if no_venue:
            return None, f"{no_venue} offer cocok tapi belum mencantumkan endpoint (venue)"
        return None, "belum ada offer yang cocok (model katalog, escrow <= 0.01, bukan miner sendiri)"
    ok.sort(key=lambda c: (not c["verified"], -c["settled"], c["min_escrow"]))
    return ok[0], ""


def brakes(state: dict, balance: Decimal) -> str:
    t = now()
    recent = [s for s in state.get("sessions", []) if t - s["ts"] < 7 * 24 * 3600 and s.get("paid", True)]
    if any(t - s["ts"] < MIN_INTERVAL for s in recent):
        return "sudah ada sesi dalam 24 jam terakhir"
    spent = sum(Decimal(s["escrow"]) for s in recent)
    if spent + MAX_ESCROW > MAX_7D:
        return f"batas 7 hari tercapai ({spent} FLOP)"
    if balance < MAX_ESCROW + FEE_RESERVE:
        return f"saldo {balance} FLOP kurang dari escrow + cadangan fee"
    return ""


def telegram(text: str) -> None:
    env = dict(os.environ)
    if REPO_ENV.exists():
        for line in REPO_ENV.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    token = env.get("TELEGRAM_BOT_TOKEN")
    ids = [x for x in env.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x]
    if not token or not ids:
        return
    for uid in ids:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": int(uid), "text": text[:3900]}, timeout=20)
        except Exception:  # noqa: BLE001 - notifikasi tidak boleh menggagalkan cron
            pass


def notify_once(state: dict, key: str, text: str) -> None:
    if state.setdefault("notified", {}).get(key):
        return
    state["notified"][key] = int(now())
    telegram(text)


def run_session(cand: dict, block: int) -> tuple[int, str]:
    env = dict(os.environ)
    env["FLOP_PW"] = ah.PW_FILE.read_text().strip()
    env["FLOP_INDEXER_URL"] = INDEXER
    prompt = (f"Dalam satu kalimat Bahasa Indonesia, jelaskan apa arti blok final {block} "
              "bagi jaringan blockchain testnet.")
    cmd = [FLOP_BIN, "--network", "testnet", "--keystore", str(ah.KEYSTORE), "--password-env", "FLOP_PW",
           "session", "run", "--miner", cand["miner"], "--endpoint", cand["endpoint"], "--model", cand["model"],
           "--prompt", prompt, "--max-flop", str(MAX_ESCROW), "--max-tokens", str(MAX_TOKENS),
           "--via", "auto", "--json"]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1800)
    return p.returncode, (p.stdout or p.stderr)[-3000:]


def main() -> int:
    dry = "--dry-run" in sys.argv
    try:
        ah.check_network()
        me = ah.address()
    except ah.Stop as e:
        print(f"STOP: {e}")
        return 2
    state = load_state()
    rows = fetch_offers()
    if rows is None:
        print("indexer offer testnet belum ada")
        return 0
    notify_once(state, "indexer_open", "FLOP: indexer offer testnet sudah terbuka. Liz mulai cek offer untuk sesi agent.")
    balance_f, _, block = ah.finalized_balance(me)
    balance = Decimal(str(balance_f))
    cand, why = choose(rows, catalog(), me, block)
    if not cand:
        print(f"belum ada kandidat: {why}")
        if not dry:
            save_state(state)
        return 0
    print(f"kandidat: miner {cand['miner']} model {cand['model']} endpoint {cand['endpoint']} "
          f"minEscrow {cand['min_escrow']} verified={cand['verified']} settled={cand['settled']}")
    stop = brakes(state, balance)
    if stop:
        print(f"rem: {stop}")
        if not dry:
            save_state(state)
        return 0
    if dry:
        print(f"dry-run: akan membuka sesi escrow {MAX_ESCROW} FLOP (saldo {balance})")
        return 0
    entry = {"ts": int(now()), "miner": cand["miner"], "model": cand["model"], "escrow": str(MAX_ESCROW),
             "block": block, "paid": True}
    state["sessions"].append(entry)  # dicatat dulu supaya rem tetap berlaku kalau proses terputus
    save_state(state)
    rc, out = run_session(cand, block)
    entry["rc"] = rc
    try:
        res = json.loads(out[out.index("{"):])
        entry["channel"] = res.get("channel") or res.get("channel_id")
        entry["ok"] = bool(res.get("ok", rc == 0))
    except (ValueError, AttributeError):
        entry["ok"] = rc == 0
    save_state(state)
    status = "BERHASIL" if entry["ok"] else "GAGAL"
    telegram(f"FLOP sesi agent {status}: miner {cand['miner'][:10]}…, model {cand['model']}, escrow {MAX_ESCROW} FLOP, "
             f"channel {entry.get('channel')}. Cek testnet.flopscan.io.")
    print(f"sesi {status} rc={rc}\n{out[-1500:]}")
    return 0 if entry["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
