"""Eksekusi transaksi EVM dari burner wallet, selalu lewat Guard."""

from decimal import Decimal

from eth_account import Account
from web3 import Web3

from .policy import Guard, PolicyError

WEI = Decimal(10) ** 18
GWEI = Decimal(10) ** 9


class EvmWallet:
    def __init__(self, private_key: str, guard: Guard) -> None:
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.guard = guard
        self._w3: dict[str, Web3] = {}

    def w3(self, chain_name: str) -> Web3:
        chain = self.guard.evm_chain(chain_name)
        if chain_name not in self._w3:
            w3 = Web3(Web3.HTTPProvider(chain["rpc"], request_kwargs={"timeout": 30}))
            if w3.eth.chain_id != int(chain["chain_id"]):
                raise PolicyError(f"RPC {chain_name} mengembalikan chain_id {w3.eth.chain_id}, bukan {chain['chain_id']}.")
            self._w3[chain_name] = w3
        return self._w3[chain_name]

    def balance(self, chain_name: str) -> Decimal:
        return Decimal(self.w3(chain_name).eth.get_balance(self.address)) / WEI

    def send(self, chain_name: str, to: str, value: str = "0", data: str = "0x", reason: str = "") -> dict:
        """Kirim transaksi (native transfer atau contract call) ke alamat yang diizinkan."""
        if not Web3.is_address(to):
            raise PolicyError(f"Alamat tujuan tidak valid: {to}")
        to = Web3.to_checksum_address(to)
        data = data or "0x"
        if not data.startswith("0x"):
            data = "0x" + data
        label = self.guard.check_evm_call(chain_name, to, data)

        chain = self.guard.evm_chain(chain_name)
        chain_key = f"evm:{chain_name}"
        w3 = self.w3(chain_name)
        value_wei = int(Decimal(str(value)) * WEI)
        if value_wei < 0:
            raise PolicyError("Nilai tidak boleh negatif.")

        tx = {"from": self.address, "to": to, "value": value_wei, "data": data}
        # estimate_gas sekaligus simulasi: transaksi yang akan revert ditolak di sini.
        try:
            gas = int(w3.eth.estimate_gas(tx) * 1.2) + 10_000
        except Exception as e:  # revert atau RPC error
            raise PolicyError(f"Simulasi gagal (transaksi kemungkinan revert): {e}") from e

        base = w3.eth.get_block("latest")["baseFeePerGas"]
        prio = w3.eth.max_priority_fee
        max_fee = 2 * base + prio
        if Decimal(max_fee) / GWEI > Decimal(str(chain.get("max_gas_gwei", 50))):
            raise PolicyError(
                f"Gas {Decimal(max_fee) / GWEI:.2f} gwei melebihi batas max_gas_gwei {chain.get('max_gas_gwei')}."
            )

        max_cost = (Decimal(value_wei) + Decimal(gas * max_fee)) / WEI
        self.guard.reserve(chain_key, max_cost)

        tx.update(
            {
                "gas": gas,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": prio,
                "nonce": w3.eth.get_transaction_count(self.address, "pending"),
                "chainId": int(chain["chain_id"]),
                "type": 2,
            }
        )
        tx.pop("from")
        signed = self.account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

        cost = (Decimal(value_wei) + Decimal(receipt["gasUsed"]) * Decimal(receipt["effectiveGasPrice"])) / WEI
        result = {
            "chain": chain_name,
            "tx_hash": "0x" + bytes(tx_hash).hex().removeprefix("0x"),
            "status": "sukses" if receipt["status"] == 1 else "GAGAL (revert)",
            "to": to,
            "to_label": label,
            "cost": f"{cost:.8f} {chain.get('native', 'ETH')}",
            "reason": reason,
        }
        self.guard.commit(chain_key, cost, result)
        return result
