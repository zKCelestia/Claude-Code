"""CLI zayro.trade (testnet, gasless).

    python -m zayro init                         # buat wallet baru di .env.zayro
    python -m zayro setup --ref KODE [--name N]  # session key + referral + username + misi
    python -m zayro daily [--notify]             # garap (untuk cron); --notify = lapor ke Telegram
    python -m zayro status                       # poin & misi
    python -m zayro bug "apa yang rusak + cara mengulanginya" [https://link]

`daily` membaca ZAYRO_REF / ZAYRO_NAME dari .env, membuat wallet sendiri kalau belum ada,
dan dengan --notify hanya mengirim pesan kalau ada yang diklaim atau ada error baru.
"""

import argparse
import sys

from dotenv import load_dotenv

from . import notify
from .client import ENV_PATH, ROOT, Zayro, ZayroError, create_wallet

LAST_ERROR = ROOT / ".zayro_last_error"


def _show(label: str, res: dict) -> None:
    ok = res.get("ok", True)
    print(f"  {'✓' if ok else '✗'} {label}" + ("" if ok else f": {res.get('reason')}"))


def cmd_init(_):
    addr = create_wallet()
    print(f"Wallet zayro dibuat. Kunci di {ENV_PATH.name} (izin 600).")
    print("Alamat:", addr)
    print("Backup file itu kalau poinnya penting buatmu.")


def cmd_setup(a):
    z = Zayro()
    print("Wallet:", z.address)
    z.ensure_session()
    print("  ✓ session key aktif")
    if a.ref:
        _show(f"referral {a.ref}", z.bind_referral(a.ref))
    if a.name:
        _show(f"username {a.name}", z.set_name(a.name))
    _show("kode referral sendiri", z.my_code())
    for mid, res in z.claim_auto_missions():
        _show(f"misi {mid}", res)
    cmd_status(a, z)


def _report(a, text: str) -> None:
    print(text)
    if a.notify:
        for err in notify.send(text):
            print("Telegram gagal:", err, file=sys.stderr)


def cmd_daily(a):
    import os

    ref = os.environ.get("ZAYRO_REF", "").strip().lower() or None
    name = os.environ.get("ZAYRO_NAME", "").strip() or None
    try:
        if not ENV_PATH.exists():
            addr = create_wallet()
            _report(a, f"🆕 Wallet zayro dibuat: {addr}\nKuncinya di {ENV_PATH.name} di VPS. Backup file itu.")
        z = Zayro()
        lines = z.autorun(ref, name)
        summary = z.summary()
    except Exception as e:  # jaringan, relayer, RPC
        msg = f"⚠️ zayro gagal: {e}"
        old = LAST_ERROR.read_text() if LAST_ERROR.exists() else ""
        LAST_ERROR.write_text(msg)
        if msg != old:  # error yang sama tidak dikirim berulang tiap jam
            _report(a, msg)
        else:
            print(msg)
        sys.exit(1)
    LAST_ERROR.unlink(missing_ok=True)
    if lines:
        _report(a, "🟢 zayro\n" + "\n".join(lines) + f"\n\nWallet: {z.address}\n{summary}")
    else:
        print("Tidak ada yang perlu diklaim.\n" + summary)


def cmd_status(_, z=None):
    z = z or Zayro()
    print("Wallet:", z.address)
    print(z.summary())


def cmd_bug(a):
    z = Zayro()
    note = " ".join(a.note.split())
    print("Laporan bug yang akan dikirim ke tim zayro:\n")
    print("  " + note)
    if a.url:
        print("  Link: " + a.url)
    print(f"\nWallet: {z.address}")
    if not a.yes and input("Kirim? (y/N) ").strip().lower() != "y":
        print("Batal, tidak ada yang dikirim.")
        return
    res = z.report_bug(note, a.url)
    if res.get("ok"):
        print("✓ Terkirim. Poin masuk kalau tim zayro mengonfirmasi bug-nya.")
    else:
        sys.exit(f"✗ Ditolak: {res.get('reason')}")


def cmd_test_notify(_):
    errors = notify.send("✅ Tes dari zayro: laporan Telegram sudah nyambung.")
    if errors:
        print("Gagal kirim ke Telegram:")
        for err in errors:
            print("  -", err)
        print("Cek TELEGRAM_BOT_TOKEN & ALLOWED_USER_IDS di .env, dan pastikan sudah kirim /start ke bot.")
        sys.exit(1)
    print("Terkirim. Cek Telegram-mu.")


def main() -> None:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser(prog="python -m zayro", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    s = sub.add_parser("setup")
    s.add_argument("--ref")
    s.add_argument("--name")
    s.set_defaults(fn=cmd_setup)
    d = sub.add_parser("daily")
    d.add_argument("--notify", action="store_true", help="kirim laporan ke Telegram")
    d.set_defaults(fn=cmd_daily)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("test-notify").set_defaults(fn=cmd_test_notify)
    b = sub.add_parser("bug", help="lapor bug ke tim zayro (misi +5000, direview manual)")
    b.add_argument("note", help="apa yang rusak dan cara mengulanginya (20-500 karakter)")
    b.add_argument("url", nargs="?", help="link screenshot/post (opsional, https://)")
    b.add_argument("-y", "--yes", action="store_true", help="kirim tanpa konfirmasi")
    b.set_defaults(fn=cmd_bug)
    a = ap.parse_args()
    try:
        a.fn(a)
    except ZayroError as e:
        sys.exit(f"Gagal: {e}")


if __name__ == "__main__":
    main()
