"""Tool burner wallet untuk agent (custom tools di Managed Agents).

Agent hanya mengirim PERMINTAAN. Penandatanganan terjadi di sini, di mesin bot,
setelah lolos Guard. Private key tidak pernah dikirim ke agent.
"""

import json
import logging
import threading
from pathlib import Path

from dotenv import dotenv_values

from .policy import Guard, PolicyError

log = logging.getLogger("burner")
ENV_PATH = Path(__file__).resolve().parent.parent / ".env.burner"
TX_LOCK = threading.Lock()  # satu transaksi burner pada satu waktu (nonce & budget aman)

TOOL_DEFS = [
    {
        "type": "custom",
        "name": "burner_status",
        "description": (
            "Lihat alamat burner wallet (EVM dan Solana), saldo per chain, sisa budget harian, "
            "daftar kontrak/program yang diizinkan, dan apakah wallet sedang di-pause. "
            "Panggil ini dulu sebelum transaksi."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "custom",
        "name": "burner_evm_send",
        "description": (
            "Kirim transaksi dari burner wallet EVM: transfer native atau panggil fungsi kontrak "
            "(misalnya mint) dengan calldata hex. Hanya ke alamat di allowed_contracts. Fungsi "
            "approve/transfer token/permit/multicall selalu ditolak. Transaksi disimulasikan dulu; "
            "kalau revert atau melebihi budget, ditolak dan alasannya dikembalikan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "chain": {"type": "string", "description": "Nama chain sesuai policy, mis. 'base'"},
                "to": {"type": "string", "description": "Alamat kontrak tujuan (0x...)"},
                "value": {"type": "string", "description": "Jumlah koin native, mis. '0.0005'. Default '0'"},
                "data": {"type": "string", "description": "Calldata hex (0x...). Kosongkan untuk transfer biasa"},
                "reason": {"type": "string", "description": "Alasan singkat transaksi ini, untuk log"},
            },
            "required": ["chain", "to", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "type": "custom",
        "name": "burner_solana_send_sol",
        "description": "Kirim SOL dari burner wallet ke penerima yang ada di allowed_recipients.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Alamat penerima"},
                "amount": {"type": "string", "description": "Jumlah SOL, mis. '0.01'"},
                "reason": {"type": "string"},
            },
            "required": ["to", "amount", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "type": "custom",
        "name": "burner_solana_sign_and_send",
        "description": (
            "Tanda tangani dan kirim transaksi Solana siap pakai (base64), misalnya dari API mint atau "
            "Blink, dengan burner wallet sebagai signer. Semua program di transaksi harus ada di "
            "allowed_programs; instruksi Transfer/Approve token ditolak. Disimulasikan dulu, dan "
            "pengeluaran SOL hasil simulasi harus muat di budget."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_base64": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["transaction_base64", "reason"],
            "additionalProperties": False,
        },
    },
]

TOOL_NAMES = {t["name"] for t in TOOL_DEFS}


class Burner:
    """Gabungan guard + wallet. Dibuat sekali oleh bot."""

    def __init__(self) -> None:
        self.guard = Guard()
        env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
        self.evm = self.sol = None
        if env.get("BURNER_EVM_PRIVATE_KEY"):
            from .evm import EvmWallet

            self.evm = EvmWallet(env["BURNER_EVM_PRIVATE_KEY"], self.guard)
        if env.get("BURNER_SOLANA_SECRET"):
            from .solana import SolanaWallet

            self.sol = SolanaWallet(env["BURNER_SOLANA_SECRET"], self.guard)
        if not (self.evm or self.sol):
            raise PolicyError(".env.burner belum ada. Jalankan: python -m burner.create_wallets")

    def status(self) -> dict:
        self.guard.reload()
        out = {"paused": self.guard.paused, "evm": {}, "solana": None}
        if self.evm:
            out["evm_address"] = self.evm.address
            for name, chain in (self.guard.policy.get("evm") or {}).items():
                key = f"evm:{name}"
                per_tx, per_day, sym = self.guard.limits(key)
                try:
                    bal = f"{self.evm.balance(name):.6f} {sym}"
                except Exception as e:
                    bal = f"error: {e}"
                out["evm"][name] = {
                    "saldo": bal,
                    "max_per_tx": f"{per_tx} {sym}",
                    "sisa_hari_ini": f"{self.guard.remaining_today(key)} / {per_day} {sym}",
                    "allowed_contracts": chain.get("allowed_contracts") or {},
                }
        if self.sol:
            sol = self.guard.policy.get("solana") or {}
            per_tx, per_day, _ = self.guard.limits("solana")
            try:
                bal = f"{self.sol.balance():.6f} SOL"
            except Exception as e:
                bal = f"error: {e}"
            out["solana"] = {
                "address": self.sol.address,
                "saldo": bal,
                "max_per_tx": f"{per_tx} SOL",
                "sisa_hari_ini": f"{self.guard.remaining_today('solana')} / {per_day} SOL",
                "allowed_programs": sol.get("allowed_programs") or {},
                "allowed_recipients": sol.get("allowed_recipients") or {},
            }
        return out

    def run_tool(self, name: str, args: dict) -> tuple[str, dict | None]:
        """Jalankan tool. Return (teks hasil untuk agent, info transaksi atau None)."""
        try:
            if name == "burner_status":
                return json.dumps(self.status(), indent=2, ensure_ascii=False), None
            with TX_LOCK:
                self.guard.reload()  # pakai policy & ledger terbaru (mis. setelah /stop)
                if name == "burner_evm_send":
                    if not self.evm:
                        raise PolicyError("Wallet EVM belum dibuat.")
                    tx = self.evm.send(
                        args["chain"], args["to"], args.get("value") or "0", args.get("data") or "0x", args.get("reason", "")
                    )
                elif name == "burner_solana_send_sol":
                    if not self.sol:
                        raise PolicyError("Wallet Solana belum dibuat.")
                    tx = self.sol.send_sol(args["to"], args["amount"], args.get("reason", ""))
                elif name == "burner_solana_sign_and_send":
                    if not self.sol:
                        raise PolicyError("Wallet Solana belum dibuat.")
                    tx = self.sol.sign_and_send(args["transaction_base64"], args.get("reason", ""))
                else:
                    return f"Tool tidak dikenal: {name}", None
            log.info("Burner tx: %s", tx)
            return json.dumps(tx, ensure_ascii=False), tx
        except PolicyError as e:
            log.warning("Burner ditolak (%s): %s", name, e)
            return f"DITOLAK oleh guard: {e}", {"rejected": True, "tool": name, "reason": str(e)}
        except KeyError as e:
            return f"Input kurang: {e}", None
        except Exception as e:
            log.exception("Burner error")
            return f"ERROR: {type(e).__name__}: {e}", None
