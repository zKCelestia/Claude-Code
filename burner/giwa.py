"""Garapan Gama (launchpad tile di GIWA Sepolia) dari burner wallet, selalu lewat Guard.

Jalankan di mesin bot (yang punya .env.burner dan burner_policy.json):

    python -m burner.giwa status
    python -m burner.giwa bridge 0.01                 # Sepolia -> GIWA Sepolia (OptimismPortal)
    python -m burner.giwa quote 0xTOKEN 0.0005
    python -m burner.giwa buy 0xTOKEN 0.0005 --slippage 10

Alamat diambil dari sumber resmi (dicek 2026-11-28):
- OptimismPortal L1: docs.giwa.io/network-information/contracts.md
- GamaLaunchpad: kontrak verified di sepolia-explorer.giwa.io, pembuat semua tile Gama.

Hanya `buy` yang didukung. `sell` di launchpad butuh approve token, dan approve selalu
diblokir guard. Tile yang sudah graduate diperdagangkan di pool DEX, bukan di launchpad.
"""

import argparse
import json
import sys
from decimal import Decimal

from web3 import Web3

from .evm import WEI
from .policy import PolicyError

L1_CHAIN = "sepolia"
L2_CHAIN = "giwa_sepolia"
GIWA_OPTIMISM_PORTAL = "0x956962C34687A954e611A83619ABaA37Ce6bC78A"  # di Ethereum Sepolia
GAMA_LAUNCHPAD = "0x7abbC4bB4Fb7aa2cEA082697E87B828A691141CB"  # di GIWA Sepolia (91342)

BUY_SELECTOR = "0xcce7ec13"  # buy(address token, uint256 minTokensOut)

LAUNCHPAD_ABI = [
    {
        "type": "function",
        "name": "quoteBuy",
        "stateMutability": "view",
        "inputs": [{"type": "address", "name": "token"}, {"type": "uint256", "name": "value"}],
        "outputs": [{"type": "uint256"}, {"type": "uint256"}, {"type": "uint256"}],
    },
    {
        "type": "function",
        "name": "curves",
        "stateMutability": "view",
        "inputs": [{"type": "address", "name": ""}],
        "outputs": [
            {"type": "address", "name": "creator"},
            {"type": "uint256", "name": ""},
            {"type": "uint256", "name": ""},
            {"type": "uint256", "name": ""},
            {"type": "uint256", "name": ""},
            {"type": "bool", "name": "graduated"},
            {"type": "uint256", "name": ""},
        ],
    },
]


def buy_calldata(token: str, min_tokens_out: int) -> str:
    """Calldata buy(token, minTokensOut) untuk GamaLaunchpad."""
    if not Web3.is_address(token):
        raise PolicyError(f"Alamat token tidak valid: {token}")
    if min_tokens_out < 0:
        raise PolicyError("minTokensOut tidak boleh negatif.")
    addr = bytes.fromhex(Web3.to_checksum_address(token)[2:]).rjust(32, b"\0")
    return BUY_SELECTOR + addr.hex() + min_tokens_out.to_bytes(32, "big").hex()


def min_out_with_slippage(quoted: int, slippage_pct: Decimal) -> int:
    if not Decimal(0) <= slippage_pct < Decimal(100):
        raise PolicyError("Slippage harus di antara 0 dan 100 persen.")
    return int(Decimal(quoted) * (Decimal(100) - slippage_pct) / Decimal(100))


def launchpad(w3: Web3):
    return w3.eth.contract(address=GAMA_LAUNCHPAD, abi=LAUNCHPAD_ABI)


def quote(w3: Web3, token: str, value_eth: str) -> dict:
    token = Web3.to_checksum_address(token)
    lp = launchpad(w3)
    curve = lp.functions.curves(token).call()
    if curve[0] == "0x0000000000000000000000000000000000000000":
        raise PolicyError(f"{token} bukan tile GamaLaunchpad.")
    if curve[5]:
        raise PolicyError(f"Tile {token} sudah graduate; beli lewat pool DEX, bukan launchpad.")
    value_wei = int(Decimal(value_eth) * WEI)
    tokens_out, fee, tax = lp.functions.quoteBuy(token, value_wei).call()
    return {"token": token, "value_wei": value_wei, "tokens_out": tokens_out, "fee_wei": fee, "snipe_tax": tax}


def _wallet():
    from .tools import Burner

    burner = Burner()
    if not burner.evm:
        raise PolicyError("Wallet EVM belum dibuat. Jalankan: python -m burner.create_wallets")
    return burner


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m burner.giwa", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="saldo burner di Sepolia & GIWA Sepolia + sisa budget")
    b = sub.add_parser("bridge", help="bridge ETH Sepolia ke GIWA Sepolia (alamat yang sama)")
    b.add_argument("amount", help="jumlah ETH, mis. 0.01")
    q = sub.add_parser("quote", help="perkiraan token yang didapat dari buy")
    q.add_argument("token")
    q.add_argument("amount")
    y = sub.add_parser("buy", help="beli tile di GamaLaunchpad")
    y.add_argument("token")
    y.add_argument("amount", help="jumlah ETH, mis. 0.0005")
    y.add_argument("--slippage", default="10", help="persen, default 10")
    args = p.parse_args(argv)

    try:
        burner = _wallet()
        wallet = burner.evm
        if args.cmd == "status":
            st = burner.status()
            out = {"evm_address": st.get("evm_address"), "paused": st["paused"]}
            out.update({k: st["evm"][k] for k in (L1_CHAIN, L2_CHAIN) if k in st["evm"]})
            print(json.dumps(out, indent=2, ensure_ascii=False))
        elif args.cmd == "bridge":
            # OptimismPortal.receive() men-deposit msg.value ke alamat pengirim di L2.
            tx = wallet.send(L1_CHAIN, GIWA_OPTIMISM_PORTAL, args.amount, "0x", "bridge Sepolia -> GIWA Sepolia")
            print(json.dumps(tx, indent=2, ensure_ascii=False))
            print("ETH biasanya masuk di GIWA Sepolia sekitar 1-3 menit kemudian.")
        elif args.cmd == "quote":
            print(json.dumps(quote(wallet.w3(L2_CHAIN), args.token, args.amount), indent=2, default=str))
        elif args.cmd == "buy":
            qt = quote(wallet.w3(L2_CHAIN), args.token, args.amount)
            min_out = min_out_with_slippage(qt["tokens_out"], Decimal(args.slippage))
            data = buy_calldata(qt["token"], min_out)
            tx = wallet.send(L2_CHAIN, GAMA_LAUNCHPAD, args.amount, data, f"Gama buy {qt['token']}")
            print(json.dumps(tx, indent=2, ensure_ascii=False))
    except PolicyError as e:
        sys.exit(f"DITOLAK: {e}")


if __name__ == "__main__":
    main()
