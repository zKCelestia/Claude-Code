"""CLI zayro.trade (testnet, gasless).

    python -m zayro init                         # buat wallet baru di .env.zayro
    python -m zayro setup --ref KODE [--name N]  # session key + referral + username + misi
    python -m zayro daily [--notify]             # garap (untuk cron); --notify = lapor ke Telegram
    python -m zayro status                       # poin & misi
    python -m zayro bug "apa yang rusak + cara mengulanginya" [https://link]
    python -m zayro mission follow               # misi X: follow | post|quote|reply|story|content URL
    python -m zayro spin                         # putar roulette sekali (manual, konfirmasi)
    python -m zayro claim ID ALAMAT_BASE|EMAIL LINK_REPLY_X

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


def cmd_spin(a):
    z = Zayro()
    season = z._get("/cases")
    cost = int(season.get("cost", 500))
    pts = int(z.points().get("points") or 0)
    if not season.get("open"):
        sys.exit("Roulette sedang tutup.")
    if pts < cost:
        sys.exit(f"Poin belum cukup: {pts} / {cost}. Tunggu check-in beberapa hari lagi.")
    print(f"Poin sekarang {pts}. Satu putaran memotong {cost} poin (posisi leaderboard bisa turun).")
    if not a.yes and input("Putar sekali? (y/N) ").strip().lower() != "y":
        print("Batal.")
        return
    res = z.spin()
    if not res.get("ok"):
        sys.exit(f"✗ Ditolak: {res.get('reason')}")
    d = res.get("draw") or {}
    print(f"🎰 Hasil: {d.get('name')} [{d.get('tier')}] (id {d.get('id')})")
    if d.get("claim"):
        print(
            "\n🎉 HADIAH ASLI! Cara klaim (dicek manual oleh tim zayro):\n"
            f"  1. Reply post roulette mereka di X dengan screenshot kemenanganmu: {season.get('claimPost')}\n"
            "  2. Lalu jalankan:\n"
            f"     bash deploy/zayro.sh claim {d.get('id')} ALAMAT_BASE_atau_EMAIL LINK_REPLY_X\n"
            "     (USDC: alamat wallet di Base mainnet milikmu. Merch: email.)"
        )
    elif d.get("prize") == "again":
        print("Dapat putaran gratis: jalankan spin lagi, poinnya dikembalikan.")
    print("\n" + z.summary())


def cmd_claim(a):
    z = Zayro()
    print(f"Klaim hadiah #{a.id} ke {a.contact}\nBukti X: {a.post}")
    if not a.yes and input("Kirim klaim? (y/N) ").strip().lower() != "y":
        print("Batal.")
        return
    res = z.claim_prize(a.id, a.contact, a.post)
    print("✓ Klaim terkirim, tunggu dicek tim zayro (maks. 24 jam)." if res.get("ok") else f"✗ Ditolak: {res.get('reason')}")


MISSION_HELP = {
    "follow": "follow @zayrotrade di X dulu, baru klaim (tanpa link)",
    "post": "link post X-mu hari ini tentang zayro",
    "quote": "link quote X-mu atas post terbaru @zayrotrade",
    "reply": "link reply X-mu di post terbaru @zayrotrade",
    "story": "link post cerita zayro-mu (direview tim)",
    "content": "link thread/video tentang zayro (direview tim)",
}


def cmd_mission(a):
    z = Zayro()
    kind = a.kind.lower()
    ms = z.missions()
    m = next((m for m in ms if m["id"] == kind), None) or next((m for m in ms if m.get("claim") == kind), None)
    if not m:
        sys.exit(f"Misi '{kind}' tidak ada. Pilihan: " + ", ".join(MISSION_HELP))
    if m.get("done"):
        print(f"Misi {m['id']} sudah selesai untuk periode ini.")
        return
    if m.get("x") and not a.url:
        sys.exit(f"Misi {m['id']} butuh link: {MISSION_HELP.get(kind, 'link post X')}")
    if a.url and not a.url.startswith("https://"):
        sys.exit("Link harus diawali https://")
    res = z.claim_mission(m["id"], url=a.url)
    pts = f" +{res['points']} poin" if res.get("points") else ""
    print(f"✓ misi {m['id']}{pts}" if res.get("ok") else f"✗ misi {m['id']}: {res.get('reason')}")


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
    mi = sub.add_parser("mission", help="klaim misi X: follow | post URL | quote URL | reply URL | story URL | content URL")
    mi.add_argument("kind")
    mi.add_argument("url", nargs="?")
    mi.set_defaults(fn=cmd_mission)
    sp = sub.add_parser("spin", help="putar roulette sekali (bayar poin)")
    sp.add_argument("-y", "--yes", action="store_true")
    sp.set_defaults(fn=cmd_spin)
    c = sub.add_parser("claim", help="klaim hadiah asli roulette")
    c.add_argument("id", type=int)
    c.add_argument("contact", help="alamat Base (USDC) atau email (merch)")
    c.add_argument("post", help="link reply-mu di X")
    c.add_argument("-y", "--yes", action="store_true")
    c.set_defaults(fn=cmd_claim)
    a = ap.parse_args()
    try:
        a.fn(a)
    except ZayroError as e:
        sys.exit(f"Gagal: {e}")


if __name__ == "__main__":
    main()
