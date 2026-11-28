"""CLI zayro.trade (testnet, gasless).

    python -m zayro init                         # buat wallet baru di .env.zayro
    python -m zayro setup --ref KODE [--name N]  # session key + referral + username + misi
    python -m zayro daily                        # check-in + misi siap klaim (pasang di cron)
    python -m zayro status                       # poin & misi
"""

import argparse
import sys

from .client import ENV_PATH, Zayro, ZayroError, create_wallet


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


def cmd_daily(a):
    z = Zayro()
    print("Wallet:", z.address)
    claimed = z.claim_auto_missions()
    for mid, res in claimed:
        _show(f"misi {mid}", res)
    if not claimed:
        print("  (tidak ada misi yang siap diklaim)")
    cmd_status(a, z)


def cmd_status(_, z=None):
    z = z or Zayro()
    p = z.points()
    print(
        f"Poin: {p.get('points')} (misi {p.get('missionPoints')}, trading {p.get('tradingPoints')}, "
        f"bonus {p.get('bonusPoints')}, referral {p.get('referralPoints')}) | rank {p.get('rank')}"
    )
    print(f"Kode referral: {p.get('code')} | referrer: {p.get('referrer')} | referee: {p.get('referees')}")
    todo = [m["id"] for m in z.missions() if not m.get("done")]
    print("Misi belum selesai:", ", ".join(todo) or "-")


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m zayro", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    s = sub.add_parser("setup")
    s.add_argument("--ref")
    s.add_argument("--name")
    s.set_defaults(fn=cmd_setup)
    sub.add_parser("daily").set_defaults(fn=cmd_daily)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    a = ap.parse_args()
    try:
        a.fn(a)
    except ZayroError as e:
        sys.exit(f"Gagal: {e}")


if __name__ == "__main__":
    main()
