"""Eksekusi transaksi Solana dari burner wallet, selalu lewat Guard.

Memakai JSON-RPC langsung (requests) + solders untuk membangun dan menandatangani.
"""

import base64
import time
from decimal import Decimal

import requests
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0, to_bytes_versioned
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

from .policy import Guard, PolicyError

LAMPORTS = Decimal(10) ** 9
FEE_MARGIN = 20_000  # lamports cadangan untuk fee/prioritas
CHAIN_KEY = "solana"


class SolanaWallet:
    def __init__(self, secret_b58: str, guard: Guard) -> None:
        self.keypair = Keypair.from_base58_string(secret_b58)
        self.address = str(self.keypair.pubkey())
        self.guard = guard

    # ---------- RPC ----------
    def _rpc(self, method: str, params: list):
        rpc = (self.guard.policy.get("solana") or {}).get("rpc")
        if not rpc:
            raise PolicyError("RPC Solana belum diisi di burner_policy.json.")
        r = requests.post(rpc, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=30)
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            raise PolicyError(f"RPC {method} error: {body['error']}")
        return body["result"]

    def _lamports(self) -> int:
        return int(self._rpc("getBalance", [self.address, {"commitment": "confirmed"}])["value"])

    def balance(self) -> Decimal:
        return Decimal(self._lamports()) / LAMPORTS

    def _blockhash(self) -> Hash:
        res = self._rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
        return Hash.from_string(res["value"]["blockhash"])

    # ---------- guard checks ----------
    def _check_programs(self, msg: MessageV0) -> None:
        keys = msg.account_keys
        self.guard.check_solana_programs(
            [(str(keys[ix.program_id_index]), bytes(ix.data)) for ix in msg.instructions]
        )

    def _simulate_spend(self, tx: VersionedTransaction) -> Decimal:
        """Simulasikan transaksi dan hitung berapa SOL berkurang dari wallet."""
        pre = self._lamports()
        res = self._rpc(
            "simulateTransaction",
            [
                base64.b64encode(bytes(tx)).decode(),
                {
                    "encoding": "base64",
                    "sigVerify": False,
                    "commitment": "confirmed",
                    "accounts": {"encoding": "base64", "addresses": [self.address]},
                },
            ],
        )["value"]
        if res.get("err"):
            logs = "\n".join((res.get("logs") or [])[-8:])
            raise PolicyError(f"Simulasi gagal: {res['err']}\n{logs}")
        post_acc = (res.get("accounts") or [None])[0]
        post = int(post_acc["lamports"]) if post_acc else 0
        return Decimal(max(0, pre - post) + FEE_MARGIN) / LAMPORTS

    def _send_and_confirm(self, tx: VersionedTransaction) -> tuple[str, str]:
        sig = self._rpc(
            "sendTransaction",
            [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}],
        )
        for _ in range(60):
            st = self._rpc("getSignatureStatuses", [[sig]])["value"][0]
            if st and st.get("confirmationStatus") in ("confirmed", "finalized"):
                return sig, ("GAGAL: " + str(st["err"])) if st.get("err") else "sukses"
            time.sleep(2)
        return sig, "belum terkonfirmasi (cek explorer)"

    def _execute(self, tx: VersionedTransaction, reason: str, extra: dict) -> dict:
        max_cost = self._simulate_spend(tx)
        self.guard.reserve(CHAIN_KEY, max_cost)
        pre = self._lamports()
        sig, status = self._send_and_confirm(tx)
        try:
            cost = Decimal(max(0, pre - self._lamports())) / LAMPORTS
        except Exception:
            cost = max_cost  # kalau gagal cek saldo, catat perkiraan terburuk
        result = {
            "chain": "solana",
            "signature": sig,
            "status": status,
            "cost": f"{cost:.9f} SOL",
            "reason": reason,
            **extra,
        }
        self.guard.commit(CHAIN_KEY, cost, result)
        return result

    # ---------- actions ----------
    def send_sol(self, to: str, amount: str, reason: str = "") -> dict:
        label = self.guard.check_solana_recipient(to)
        lamports = int(Decimal(str(amount)) * LAMPORTS)
        if lamports <= 0:
            raise PolicyError("Jumlah harus lebih dari 0.")
        ix = transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=Pubkey.from_string(to), lamports=lamports))
        msg = MessageV0.try_compile(self.keypair.pubkey(), [ix], [], self._blockhash())
        self._check_programs(msg)
        tx = VersionedTransaction(msg, [self.keypair])
        return self._execute(tx, reason, {"to": to, "to_label": label})

    def sign_and_send(self, tx_base64: str, reason: str = "") -> dict:
        """Tanda tangani transaksi siap pakai (mis. dari API mint) sebagai salah satu signer."""
        try:
            tx = VersionedTransaction.from_bytes(base64.b64decode(tx_base64))
        except Exception as e:
            raise PolicyError(f"Transaksi base64 tidak valid: {e}") from e
        msg = tx.message
        self._check_programs(msg)

        keys = list(msg.account_keys)
        me = self.keypair.pubkey()
        n_signers = msg.header.num_required_signatures
        if me not in keys[:n_signers]:
            raise PolicyError("Burner wallet bukan signer di transaksi ini.")
        idx = keys.index(me)

        sigs = list(tx.signatures)
        while len(sigs) < n_signers:
            sigs.append(Signature.default())
        sigs[idx] = self.keypair.sign_message(to_bytes_versioned(msg))
        missing = [str(keys[i]) for i in range(n_signers) if i != idx and sigs[i] == Signature.default()]
        if missing:
            raise PolicyError(f"Transaksi masih butuh tanda tangan lain: {', '.join(missing)}")
        signed = VersionedTransaction.populate(msg, sigs)
        return self._execute(signed, reason, {})
