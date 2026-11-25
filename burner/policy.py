"""Guard untuk burner wallet: policy, batas pengeluaran, kill switch, dan ledger.

Semua transaksi WAJIB lewat `Guard.reserve()` sebelum ditandatangani dan
`Guard.commit()` sesudah terkirim. Guard menolak (raise PolicyError) bila:
- wallet sedang di-pause (/stop),
- chain atau kontrak/program tidak ada di daftar izin,
- biaya maksimum transaksi melebihi batas per transaksi,
- total hari ini (UTC) akan melebihi batas harian.
"""

import json
import threading
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "burner_policy.json"
LEDGER_PATH = ROOT / "burner_ledger.json"

# Selector EVM yang dipakai drainer: approval, transfer token, permit, dan pembungkus multicall.
BLOCKED_EVM_SELECTORS = {
    "0x095ea7b3": "approve",
    "0xa22cb465": "setApprovalForAll",
    "0x39509351": "increaseAllowance",
    "0xd505accf": "permit",
    "0x8fcbaf0c": "permit (DAI)",
    "0xa9059cbb": "transfer (token)",
    "0x23b872dd": "transferFrom",
    "0x42842e0e": "safeTransferFrom",
    "0xb88d4fde": "safeTransferFrom (data)",
    "0xf242432a": "safeTransferFrom (ERC1155)",
    "0x2eb2c2d6": "safeBatchTransferFrom",
    "0xac9650d8": "multicall",
    "0x5ae401dc": "multicall (deadline)",
    "0x252dba42": "aggregate",
    "0x82ad56cb": "aggregate3",
    "0x174dea71": "aggregate3Value",
}

TOKEN_PROGRAMS = {
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
}
# Instruksi SPL Token yang bisa memindahkan/menyerahkan token milik wallet.
BLOCKED_TOKEN_IX = {
    3: "Transfer",
    4: "Approve",
    6: "SetAuthority",
    12: "TransferChecked",
    13: "ApproveChecked",
}


class PolicyError(Exception):
    """Transaksi ditolak oleh guard."""


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class Guard:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reload()

    # ---------- state ----------
    def reload(self) -> None:
        if not POLICY_PATH.exists():
            raise PolicyError(
                "burner_policy.json belum ada. Salin dari burner/policy.example.json lalu sesuaikan."
            )
        self.policy = json.loads(POLICY_PATH.read_text())
        self.ledger = (
            json.loads(LEDGER_PATH.read_text())
            if LEDGER_PATH.exists()
            else {"paused": False, "spent": {}, "history": []}
        )

    def _save(self) -> None:
        tmp = LEDGER_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.ledger, indent=2))
        tmp.replace(LEDGER_PATH)

    @property
    def paused(self) -> bool:
        return bool(self.ledger.get("paused"))

    def set_paused(self, value: bool) -> None:
        with self._lock:
            self.ledger["paused"] = value
            self._save()

    # ---------- limits ----------
    def limits(self, chain_key: str) -> tuple[Decimal, Decimal, str]:
        """(max_per_tx, max_per_day, symbol) untuk 'solana' atau 'evm:<nama>'."""
        if chain_key == "solana":
            c = self.policy.get("solana") or {}
            sym = "SOL"
        else:
            c = self.evm_chain(chain_key.split(":", 1)[1])
            sym = c.get("native", "ETH")
        return Decimal(str(c["max_per_tx"])), Decimal(str(c["max_per_day"])), sym

    def spent_today(self, chain_key: str) -> Decimal:
        return Decimal(self.ledger["spent"].get(_today(), {}).get(chain_key, "0"))

    def remaining_today(self, chain_key: str) -> Decimal:
        _, per_day, _ = self.limits(chain_key)
        return max(Decimal(0), per_day - self.spent_today(chain_key))

    # ---------- allowlists ----------
    def evm_chain(self, name: str) -> dict:
        chains = self.policy.get("evm") or {}
        if name not in chains:
            raise PolicyError(f"Chain EVM '{name}' tidak ada di policy. Yang diizinkan: {', '.join(chains) or '-'}")
        return chains[name]

    def check_evm_call(self, chain_name: str, to: str, data: str) -> str:
        chain = self.evm_chain(chain_name)
        allowed = {a.lower(): label for a, label in (chain.get("allowed_contracts") or {}).items()}
        if to.lower() not in allowed:
            raise PolicyError(f"Alamat {to} tidak ada di allowed_contracts untuk {chain_name}.")
        selector = (data or "0x")[:10].lower()
        if selector in BLOCKED_EVM_SELECTORS:
            raise PolicyError(
                f"Fungsi {BLOCKED_EVM_SELECTORS[selector]} ({selector}) selalu diblokir "
                "karena bisa menguras aset."
            )
        return allowed[to.lower()]

    def check_solana_programs(self, program_ids_and_data: list[tuple[str, bytes]]) -> None:
        allowed = (self.policy.get("solana") or {}).get("allowed_programs") or {}
        for pid, data in program_ids_and_data:
            if pid not in allowed:
                raise PolicyError(f"Program Solana {pid} tidak ada di allowed_programs.")
            if pid in TOKEN_PROGRAMS and data and data[0] in BLOCKED_TOKEN_IX:
                raise PolicyError(
                    f"Instruksi token {BLOCKED_TOKEN_IX[data[0]]} diblokir karena bisa memindahkan token wallet."
                )

    def check_solana_recipient(self, to: str) -> str:
        allowed = (self.policy.get("solana") or {}).get("allowed_recipients") or {}
        if to not in allowed:
            raise PolicyError(f"Penerima SOL {to} tidak ada di allowed_recipients.")
        return allowed[to]

    # ---------- spend accounting ----------
    def reserve(self, chain_key: str, max_cost: Decimal) -> None:
        """Pastikan biaya maksimum transaksi muat di batas per-tx dan sisa harian."""
        with self._lock:
            if self.paused:
                raise PolicyError("Burner wallet sedang di-pause (/stop). Pakai /resume untuk lanjut.")
            per_tx, per_day, sym = self.limits(chain_key)
            if max_cost > per_tx:
                raise PolicyError(f"Biaya maks {max_cost:.8f} {sym} melebihi batas per transaksi {per_tx} {sym}.")
            if self.spent_today(chain_key) + max_cost > per_day:
                raise PolicyError(
                    f"Melebihi batas harian {per_day} {sym} "
                    f"(terpakai {self.spent_today(chain_key):.8f}, butuh {max_cost:.8f})."
                )

    def commit(self, chain_key: str, cost: Decimal, entry: dict) -> None:
        with self._lock:
            day = self.ledger["spent"].setdefault(_today(), {})
            day[chain_key] = str(Decimal(day.get(chain_key, "0")) + cost)
            entry = {"time": datetime.now(timezone.utc).isoformat(), "chain": chain_key, "cost": str(cost), **entry}
            self.ledger["history"].append(entry)
            self.ledger["history"] = self.ledger["history"][-500:]
            self._save()
