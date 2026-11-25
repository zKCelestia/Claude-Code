"""Buat burner wallet EVM + Solana. Jalankan di mesin yang menjalankan bot:

    python -m burner.create_wallets

- Private key ditulis ke .env.burner (izin file 600) dan TIDAK dicetak ke layar.
- Script menolak menimpa .env.burner yang sudah ada, supaya wallet berisi dana tidak hilang.
- Yang dicetak hanya alamat publik, untuk diisi saldo kecil.
"""

import os
import sys
from pathlib import Path

from eth_account import Account
from solders.keypair import Keypair

ENV_PATH = Path(__file__).resolve().parent.parent / ".env.burner"


def main() -> None:
    if ENV_PATH.exists():
        sys.exit(
            f"{ENV_PATH.name} sudah ada, tidak ditimpa. Kalau memang mau wallet baru, "
            "pindahkan sisa dana dulu, lalu hapus atau ganti nama file itu secara manual."
        )

    evm = Account.create()
    sol = Keypair()

    content = (
        "# BURNER WALLET - RAHASIA. Jangan commit, jangan kirim ke chat siapa pun.\n"
        f"BURNER_EVM_PRIVATE_KEY={evm.key.hex()}\n"
        f"BURNER_SOLANA_SECRET={sol}\n"
    )
    # Buat file dengan izin 600 sejak awal (bukan chmod belakangan).
    fd = os.open(ENV_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(content)

    print("Burner wallet dibuat. Private key tersimpan di", ENV_PATH.name, "(izin 600).")
    print()
    print("Alamat EVM    :", evm.address)
    print("Alamat Solana :", sol.pubkey())
    print()
    print("Isi saldo SEPERLUNYA saja (cukup untuk gas + mint).")
    print("Backup .env.burner di tempat aman kalau saldonya penting buatmu.")


if __name__ == "__main__":
    main()
