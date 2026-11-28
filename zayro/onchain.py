"""Otomasi on-chain zayro (testnet GIWA Sepolia): swap ETH -> test USDC dan trade kecil.

- Swap = transfer ETH ke alamat swap relayer zayro. Ini transaksi on-chain, jadi WAJIB
  lewat Guard (burner/policy.py) dengan policy sendiri: `zayro_policy.json` (batas harian,
  allowlist alamat) dan ledger `zayro_ledger.json`. Tidak ada jalan pintas di luar Guard.
- Trade = intent EIP-712 yang ditandatangani session key lalu dikirim relayer (gasless).
  Session key tidak bisa withdraw dana.
- Stake ZAYRO butuh approve(); Guard memblokir approve, jadi stake TIDAK diotomatiskan.
"""

import json
import os
import secrets
import time
from datetime import datetime, timezone
from decimal import Decimal

from eth_account.messages import encode_typed_data
from web3 import Web3

from burner.evm import EvmWallet
from burner.policy import Guard, PolicyError

from .client import CHAIN_ID, ROOT, RPC, Zayro, ZayroError

POLICY_PATH = ROOT / "zayro_policy.json"
LEDGER_PATH = ROOT / "zayro_ledger.json"
STATE_PATH = ROOT / ".zayro_state.json"

CHAIN = "giwa-sepolia"
EXCHANGE = "0x77b52F32958d2b62BfB6FB090EFd572e5c547f7B"
ORDERS = "0x7C24FE052B983925cE64bb6e1Ef4A05F02dAB18a"
SWAP_TO = "0x0182557Aca1353f2e9956CEdd65d16d74ed6B34a"  # relayer zayro (health.swap.to)
USDC_DEC = 6

DEFAULT_POLICY = {
    "_catatan": "Policy wallet zayro (testnet). Swap ETH hanya ke alamat di allowed_contracts.",
    "evm": {
        CHAIN: {
            "chain_id": CHAIN_ID,
            "rpc": RPC,
            "native": "ETH",
            "max_per_tx": "0.11",
            "max_per_day": "0.2",
            "max_gas_gwei": 1,
            "allowed_contracts": {SWAP_TO: "zayro swap (relayer): ETH -> test USDC"},
        }
    },
}

# Trade harian (ZAYRO_TRADES_PER_DAY kali, satu per jam): posisi minimum zayro ($10 margin x 50 = $500), ditahan sebentar lalu ditutup.
TRADE_MARGIN = 10
TRADE_LEVERAGE = 50
TRADE_HOLD_S = 30
GAS_RESERVE_ETH = Decimal("0.002")

EXCHANGE_ABI = [
    {"name": "balances", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]},
]

DOMAIN_TYPE = [
    {"name": "name", "type": "string"},
    {"name": "version", "type": "string"},
    {"name": "chainId", "type": "uint256"},
    {"name": "verifyingContract", "type": "address"},
]
OPEN_TYPE = [
    {"name": "user", "type": "address"},
    {"name": "instrumentId", "type": "uint32"},
    {"name": "isLong", "type": "bool"},
    {"name": "fromQueued", "type": "bool"},
    {"name": "leverage", "type": "uint32"},
    {"name": "margin", "type": "uint128"},
    {"name": "limitPrice", "type": "uint256"},
    {"name": "deadline", "type": "uint64"},
    {"name": "nonce", "type": "uint256"},
]
CLOSE_TYPE = [
    {"name": "user", "type": "address"},
    {"name": "positionId", "type": "uint256"},
    {"name": "limitPrice", "type": "uint256"},
    {"name": "deadline", "type": "uint64"},
    {"name": "nonce", "type": "uint256"},
]


def trades_per_day() -> int:
    """ZAYRO_TRADES_PER_DAY di .env (default 1). Cron jalan tiap jam, jadi maksimal 24."""
    try:
        n = int(os.environ.get("ZAYRO_TRADES_PER_DAY", "1"))
    except ValueError:
        n = 1
    return max(0, min(24, n))


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_state(st: dict) -> None:
    STATE_PATH.write_text(json.dumps(st))


class ZayroChain:
    def __init__(self, z: Zayro, sleep=time.sleep) -> None:
        if not POLICY_PATH.exists():
            POLICY_PATH.write_text(json.dumps(DEFAULT_POLICY, indent=2))
        self.z = z
        self.sleep = sleep
        self.guard = Guard(POLICY_PATH, LEDGER_PATH)
        self.wallet = EvmWallet(z.env["ZAYRO_PRIVATE_KEY"], self.guard)

    # ---------- baca ----------
    @property
    def w3(self) -> Web3:
        return self.wallet.w3(CHAIN)

    def eth_balance(self) -> Decimal:
        return self.wallet.balance(CHAIN)

    def usdc_balance(self) -> Decimal:
        c = self.w3.eth.contract(address=Web3.to_checksum_address(EXCHANGE), abi=EXCHANGE_ABI)
        return Decimal(c.functions.balances(self.z.address).call()) / Decimal(10**USDC_DEC)

    def account(self) -> dict:
        return self.z._get(f"/account/{self.z.address}")

    # ---------- swap ETH -> test USDC (on-chain, lewat Guard) ----------
    def swap_available(self) -> list[str]:
        """Swap ETH yang tersedia (sisakan cadangan gas) ke test USDC."""
        health = self.z.health()
        sw = health.get("swap") or {}
        if not sw.get("open"):
            return []
        if Web3.to_checksum_address(sw.get("to", "0x" + "0" * 40)) != Web3.to_checksum_address(SWAP_TO):
            return [f"✗ swap: alamat swap zayro berubah ke {sw.get('to')}, tidak dikirim (cek manual)"]
        rate = Decimal(str(sw.get("rate", "0")))
        left = Decimal(str(self.z._get(f"/swap/{self.z.address}").get("left", "0"))) / Decimal(10**USDC_DEC)
        if rate <= 0 or left <= 0:
            return []
        eth = min(self.eth_balance() - GAS_RESERVE_ETH, left / rate)
        eth = eth.quantize(Decimal("0.000001"), rounding="ROUND_DOWN")
        if eth * Decimal(10**18) < Decimal(str(sw.get("minWei", "1000000000000000"))):
            return []
        tx = self.wallet.send(CHAIN, SWAP_TO, value=str(eth), reason="zayro swap ETH -> test USDC")
        if tx["status"] != "sukses":
            return [f"✗ swap {eth} ETH revert ({tx['tx_hash']})"]
        for _ in range(8):
            res = self.z._post("/swap", {"hash": tx["tx_hash"]})
            if res.get("ok"):
                usdc = Decimal(str(res.get("amount", "0"))) / Decimal(10**USDC_DEC)
                return [f"✓ swap {eth} ETH -> {usdc:,.0f} test USDC"]
            if not res.get("pending"):
                return [f"✗ swap {eth} ETH: {res.get('reason')} (tx {tx['tx_hash']})"]
            self.sleep(10)
        return [f"… swap {eth} ETH terkirim, USDC masuk dalam beberapa menit (tx {tx['tx_hash']})"]

    # ---------- trade (gasless, ditandatangani session key) ----------
    def _sign_intent(self, primary: str, fields: list, message: dict) -> str:
        sk = self.z.ensure_session()
        typed = {
            "types": {"EIP712Domain": DOMAIN_TYPE, primary: fields},
            "primaryType": primary,
            "domain": {"name": "Zayro Orders", "version": "2", "chainId": CHAIN_ID, "verifyingContract": ORDERS},
            "message": message,
        }
        sig = sk.sign_message(encode_typed_data(full_message=typed)).signature.hex()
        return sig if sig.startswith("0x") else "0x" + sig

    def open_intent(self, instrument_id: int, is_long: bool, margin: int, leverage: int) -> dict:
        msg = {
            "user": self.z.address,
            "instrumentId": instrument_id,
            "isLong": is_long,
            "fromQueued": False,
            "leverage": leverage,
            "margin": margin * 10**USDC_DEC,
            "limitPrice": 0,
            "deadline": int(time.time()) + 300,
            "nonce": secrets.randbits(256),
        }
        sig = self._sign_intent("OpenIntent", OPEN_TYPE, msg)
        intent = {**msg, "margin": str(msg["margin"]), "limitPrice": "0", "deadline": str(msg["deadline"]), "nonce": str(msg["nonce"])}
        return {"intent": intent, "signature": sig}

    def close_intent(self, position_id: int) -> dict:
        msg = {
            "user": self.z.address,
            "positionId": int(position_id),
            "limitPrice": 0,
            "deadline": int(time.time()) + 300,
            "nonce": secrets.randbits(256),
        }
        sig = self._sign_intent("CloseIntent", CLOSE_TYPE, msg)
        intent = {"user": msg["user"], "positionId": str(position_id), "limitPrice": "0", "deadline": str(msg["deadline"]), "nonce": str(msg["nonce"])}
        return {"intent": intent, "signature": sig}

    def _wait(self, check, tries: int = 12, every: float = 5):
        for _ in range(tries):
            got = check()
            if got:
                return got
            self.sleep(every)
        return None

    def trade_once(self, coin: str = "BTC") -> list[str]:
        health = self.z.health()
        market = next((m for m in health.get("markets", []) if m["coin"] == coin), None)
        if not market or market.get("retired") or market.get("opensPaused"):
            return [f"✗ trade: market {coin} sedang tidak dibuka"]
        before = {p["id"] for p in self.account().get("positions", [])}
        is_long = secrets.randbits(1) == 1
        side = "long" if is_long else "short"
        res = self.z._post("/open", self.open_intent(market["instrumentId"], is_long, TRADE_MARGIN, TRADE_LEVERAGE))
        if not res.get("ok") and not res.get("pending"):
            return [f"✗ buka {coin} {side}: {res.get('reason')}"]
        pos = self._wait(lambda: next((p for p in self.account().get("positions", []) if p["id"] not in before), None))
        if not pos:
            return [f"… buka {coin} {side} {TRADE_LEVERAGE}× belum terisi; margin dikembalikan kalau gagal"]
        self.sleep(TRADE_HOLD_S)
        res = self.z._post("/close", self.close_intent(int(pos["id"])))
        if not res.get("ok") and not res.get("pending"):
            return [f"✗ tutup posisi #{pos['id']}: {res.get('reason')} (tutup manual di web)"]
        done = self._wait(lambda: next((h for h in self.account().get("history", []) if h["id"] == pos["id"]), None))
        if not done:
            return [f"… posisi #{pos['id']} sedang ditutup"]
        pnl = Decimal(done["pnl"]) / Decimal(10**USDC_DEC)
        minted = Decimal(done.get("minted") or 0) / Decimal(10**18)
        extra = f", +{minted:,.0f} ZAYRO" if minted > 0 else ""
        return [f"✓ trade {coin} {side} {TRADE_LEVERAGE}× ${TRADE_MARGIN}: PnL {pnl:+.2f} USDC{extra}"]

    # ---------- satu putaran on-chain ----------
    def autorun(self) -> list[str]:
        lines: list[str] = []
        try:
            lines += self.swap_available()
        except PolicyError as e:
            lines.append(f"✗ swap ditolak guard: {e}")
        st = _state()
        if st.get("trade_day") != _today():
            st = {"trade_day": _today(), "trades": 0}
        if st["trades"] < trades_per_day() and self.usdc_balance() >= TRADE_MARGIN:
            st["trades"] += 1
            _save_state(st)  # catat dulu: jatah harian tetap terhitung walau trade error
            lines += self.trade_once()
        return lines

    def summary(self) -> str:
        return f"On-chain: {self.eth_balance():.4f} ETH | {self.usdc_balance():,.2f} test USDC di exchange"


__all__ = ["ZayroChain", "ZayroError"]
