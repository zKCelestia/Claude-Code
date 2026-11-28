"""Klien relayer zayro.trade (testnet GIWA Sepolia).

Semua aksi di sini GASLESS: cuma tanda tangan (EIP-712 / personal_sign) yang dikirim
ke relayer zayro. Modul ini sengaja TIDAK pernah mengirim transaksi on-chain, jadi
tidak ada dana yang bisa keluar dari wallet lewat sini. Kalau nanti butuh transaksi
on-chain (swap ETH ke USDC, deposit), lewatkan lewat guard di `burner/`.

Wallet zayro terpisah dari burner: kuncinya di `.env.zayro` (izin 600, jangan commit).
"""

import os
import time
from pathlib import Path

import requests
from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data
from web3 import Web3

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env.zayro"

API = "https://zayro.trade/api-giwa"
RPC = "https://sepolia-rpc.giwa.io"
CHAIN_ID = 91342
SESSION_KEYS = "0x33afd8645F67aE0587e2Fd2bBbF21B1dc7E72826"
ZERO = "0x0000000000000000000000000000000000000000"
SESSION_DAYS = 29  # sama dengan web zayro
RENEW_BEFORE = 2 * 86400  # perpanjang session key kalau sisa < 2 hari

# Misi yang bisa diklaim tanpa X/review manual.
AUTO_CLAIMS = {"checkin", "staked", "referred", "name", "trade", "invite"}

NONCES_ABI = [
    {
        "name": "nonces",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "user", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    }
]


class ZayroError(Exception):
    pass


# --- penyimpanan kunci -------------------------------------------------------


def _read_env(path: Path = ENV_PATH) -> dict:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _write_env(data: dict, path: Path = ENV_PATH) -> None:
    body = "# WALLET ZAYRO (testnet) - RAHASIA. Jangan commit, jangan kirim ke chat siapa pun.\n"
    body += "".join(f"{k}={v}\n" for k, v in data.items())
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(body)
    os.replace(tmp, path)


def create_wallet(path: Path = ENV_PATH) -> str:
    """Buat wallet baru. Menolak menimpa file yang sudah ada."""
    if path.exists():
        raise ZayroError(f"{path.name} sudah ada, tidak ditimpa.")
    acct = Account.create()
    _write_env({"ZAYRO_PRIVATE_KEY": acct.key.hex()}, path)
    return acct.address


def _line(label: str, res: dict) -> str:
    return f"✓ {label}" if res.get("ok") else f"✗ {label}: {res.get('reason')}"


# --- klien -------------------------------------------------------------------


class Zayro:
    def __init__(self, path: Path = ENV_PATH, api: str = API, rpc: str = RPC, http=None) -> None:
        self.path = path
        self.env = _read_env(path)
        if "ZAYRO_PRIVATE_KEY" not in self.env:
            raise ZayroError(f"{path.name} belum ada. Jalankan dulu: python -m zayro init")
        self.account = Account.from_key(self.env["ZAYRO_PRIVATE_KEY"])
        self.address = self.account.address
        self.api = api
        self.rpc = rpc
        self.http = http or requests.Session()

    # HTTP
    def _get(self, route: str) -> dict:
        r = self.http.get(self.api + route, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, route: str, body: dict, tries: int = 4) -> dict:
        for i in range(tries):
            r = self.http.post(self.api + route, json=body, timeout=30)
            try:
                data = r.json()
            except ValueError:
                data = {}
            if r.ok and data.get("ok", True):
                return data
            reason = str(data.get("reason") or data.get("error") or f"HTTP {r.status_code}")
            # Relayer sibuk = belum ada yang dikirim, aman diulang.
            if "busy" not in reason.lower() or i == tries - 1:
                return {**data, "ok": False, "reason": reason}
            time.sleep(8)

    # baca
    def health(self) -> dict:
        return self._get("/health")

    def points(self) -> dict:
        return self._get(f"/points/{self.address}")

    def missions(self) -> list:
        return self._get(f"/missions/{self.address}").get("missions", [])

    # session key
    def _session(self):
        key = self.env.get("ZAYRO_SESSION_KEY")
        expiry = int(self.env.get("ZAYRO_SESSION_EXPIRY", "0"))
        if key and expiry - time.time() > RENEW_BEFORE:
            return Account.from_key(key)
        return None

    def _nonce(self) -> int:
        w3 = Web3(Web3.HTTPProvider(self.rpc, request_kwargs={"timeout": 30}))
        if w3.eth.chain_id != CHAIN_ID:
            raise ZayroError(f"RPC mengembalikan chain_id {w3.eth.chain_id}, bukan {CHAIN_ID}.")
        c = w3.eth.contract(address=Web3.to_checksum_address(SESSION_KEYS), abi=NONCES_ABI)
        return c.functions.nonces(self.address).call()

    def register_session(self, nonce: int | None = None) -> dict:
        """Daftarkan session key baru (gasless). Session key tidak bisa withdraw dana."""
        sk = Account.create()
        expiry = int(time.time()) + SESSION_DAYS * 86400
        if nonce is None:
            nonce = self._nonce()
        typed = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "RegisterSessionKey": [
                    {"name": "user", "type": "address"},
                    {"name": "sessionKey", "type": "address"},
                    {"name": "feeAddress", "type": "address"},
                    {"name": "expiry", "type": "uint64"},
                    {"name": "nonce", "type": "uint256"},
                ],
            },
            "primaryType": "RegisterSessionKey",
            "domain": {
                "name": "Zayro SessionKeyManager",
                "version": "2",
                "chainId": CHAIN_ID,
                "verifyingContract": SESSION_KEYS,
            },
            "message": {
                "user": self.address,
                "sessionKey": sk.address,
                "feeAddress": ZERO,
                "expiry": expiry,
                "nonce": nonce,
            },
        }
        sig = self.account.sign_message(encode_typed_data(full_message=typed)).signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        res = self._post(
            "/session-key",
            {"user": self.address, "sessionKey": sk.address, "feeAddress": ZERO, "expiry": str(expiry), "signature": sig},
        )
        if not res.get("ok"):
            raise ZayroError(f"Relayer menolak session key: {res.get('reason')}")
        self.env["ZAYRO_SESSION_KEY"] = sk.key.hex()
        self.env["ZAYRO_SESSION_EXPIRY"] = str(expiry)
        _write_env(self.env, self.path)
        return res

    def ensure_session(self):
        return self._session() or (self.register_session() and self._session())

    def session_sign(self, message: str) -> dict:
        sk = self.ensure_session()
        sig = sk.sign_message(encode_defunct(text=message)).signature.hex()
        return {"sessionKey": sk.address, "signature": sig if sig.startswith("0x") else "0x" + sig}

    # aksi
    def _addr(self) -> str:
        return self.address.lower()

    def bind_referral(self, code: str) -> dict:
        code = code.strip().lower()
        msg = f"zayro referral: {self._addr()} joins with code {code}"
        return self._post("/referral/bind", {"user": self.address, **self.session_sign(msg), "code": code})

    def my_code(self) -> dict:
        return self._post("/referral/code", {"user": self.address, **self.session_sign(f"zayro code: {self._addr()}")})

    def set_name(self, name: str) -> dict:
        at = int(time.time() * 1000)
        msg = f"zayro name: {self._addr()} {name} at {at}"
        return self._post("/names", {"user": self.address, **self.session_sign(msg), "name": name, "at": at})

    def claim_mission(self, mission_id: str, url: str | None = None, note: str | None = None) -> dict:
        at = int(time.time() * 1000)
        msg = f"zayro mission: {self._addr()} {mission_id} at {at}"
        body = {"user": self.address, **self.session_sign(msg), "mission": mission_id, "at": at}
        if url:
            body["url"] = url
        if note:
            body["note"] = note
        return self._post("/missions/claim", body)

    def spin(self) -> dict:
        """Putar roulette sekali (bayar poin, biasanya 500). Hasil: {'ok', 'draw': {...}}."""
        at = int(time.time() * 1000)
        msg = f"zayro case: {self._addr()} at {at}"
        return self._post("/cases", {"user": self.address, **self.session_sign(msg), "at": at})

    def claim_prize(self, draw_id: int, contact: str, post: str) -> dict:
        """Klaim hadiah asli. contact = alamat Base (USDC) atau email (merch); post = link reply di X."""
        at = int(time.time() * 1000)
        contact, post = contact.strip(), post.strip()
        msg = f"zayro case claim: {self._addr()} {draw_id} to {contact} at {at}"
        return self._post(
            "/cases/claim", {"user": self.address, **self.session_sign(msg), "id": draw_id, "contact": contact, "post": post, "at": at}
        )

    def report_bug(self, note: str, url: str | None = None) -> dict:
        """Kirim laporan bug (misi 'bug', direview tim zayro). Tulis manual: apa yang rusak + cara mengulanginya."""
        note = " ".join(note.split())
        if not 20 <= len(note) <= 500:
            raise ZayroError(f"Laporan harus 20-500 karakter (sekarang {len(note)}).")
        if url and not url.startswith("https://"):
            raise ZayroError("Link harus diawali https://")
        return self.claim_mission("bug", url=url, note=note)

    def autorun(self, ref: str | None = None, name: str | None = None) -> list[str]:
        """Satu putaran otomatis (aman diulang tiap jam): session key, referral dan
        username kalau belum, lalu klaim misi yang siap. Mengembalikan baris laporan
        hanya untuk hal yang benar-benar dikerjakan; list kosong = tidak ada kerjaan."""
        tried = self.__dict__.setdefault("_tried", set())
        lines = []
        self.ensure_session()
        if ref and ref not in tried and self.points().get("referrer") is None:
            tried.add(ref)
            res = self.bind_referral(ref)
            lines.append(_line(f"referral {ref}", res))
        if name and name not in tried:
            tried.add(name)
            m = next((m for m in self.missions() if m.get("claim") == "name"), None)
            if m and not m.get("done"):
                lines.append(_line(f"username {name}", self.set_name(name)))
        for mid, res in self.claim_auto_missions():
            if res.get("ok") or mid not in tried:  # gagal yang sama cukup dilaporkan sekali
                lines.append(_line(f"misi {mid}" + (f" +{res['points']}" if res.get("points") else ""), res))
            if not res.get("ok"):
                tried.add(mid)
        return lines

    def summary(self) -> str:
        p = self.points()
        todo = [m["id"] for m in self.missions() if not m.get("done")]
        return (
            f"Poin: {p.get('points')} | rank {p.get('rank')}\n"
            f"Kode referral: {p.get('code')} | referrer: {p.get('referrer') or '-'} | referee: {p.get('referees')}\n"
            f"Misi belum selesai: {', '.join(todo) or '-'}"
        )

    def claim_auto_missions(self) -> list[tuple[str, dict]]:
        """Klaim semua misi yang siap dan tidak butuh X/review. Check-in selalu dicoba."""
        done = []
        for m in self.missions():
            if m.get("done") or m.get("x") or m.get("claim") not in AUTO_CLAIMS:
                continue
            if m.get("ready") or m.get("claim") == "checkin":
                done.append((m["id"], self.claim_mission(m["id"])))
        return done
