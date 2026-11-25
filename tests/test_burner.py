"""Test guard burner wallet.

EVM diuji dengan chain lokal (eth-tester): transaksi benar-benar ditandatangani dan dieksekusi.
Solana diuji dengan RPC tiruan: transaksi asli dibangun dan ditandatangani dengan solders.

    pip install "web3[tester]" pytest
    pytest tests/
"""

import base64
import json
from decimal import Decimal

import pytest
from eth_account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from web3 import EthereumTesterProvider, Web3

import burner.policy as policy_mod
from burner.evm import EvmWallet
from burner.policy import Guard, PolicyError
from burner.solana import SolanaWallet

# Kontrak mini: runtime STOP (semua call sukses) dan runtime REVERT.
OK_INITCODE = "0x6001600c60003960016000f300"
REVERT_INITCODE = "0x6005600c60003960056000f360006000fd"
MINT_DATA = "0x1249c58b"  # mint()
APPROVE_DATA = "0x095ea7b3" + "00" * 64


def write_policy(tmp_path, evm=None, solana=None):
    pol = {"evm": evm or {}, "solana": solana or {}}
    (tmp_path / "burner_policy.json").write_text(json.dumps(pol))


@pytest.fixture
def paths(tmp_path, monkeypatch):
    monkeypatch.setattr(policy_mod, "POLICY_PATH", tmp_path / "burner_policy.json")
    monkeypatch.setattr(policy_mod, "LEDGER_PATH", tmp_path / "burner_ledger.json")
    return tmp_path


# ---------------------------------------------------------------- EVM
@pytest.fixture
def evm(paths, monkeypatch):
    w3 = Web3(EthereumTesterProvider())
    funder = w3.eth.accounts[0]

    def deploy(code):
        h = w3.eth.send_transaction({"from": funder, "data": code})
        return w3.eth.wait_for_transaction_receipt(h)["contractAddress"]

    ok, bad = deploy(OK_INITCODE), deploy(REVERT_INITCODE)
    stranger = Account.create().address
    acct = Account.create()
    w3.eth.wait_for_transaction_receipt(
        w3.eth.send_transaction({"from": funder, "to": acct.address, "value": w3.to_wei(1, "ether")})
    )

    def make(max_per_tx="0.01", max_per_day="0.012", max_gas_gwei=10):
        write_policy(
            paths,
            evm={
                "local": {
                    "chain_id": w3.eth.chain_id,
                    "rpc": "http://unused",
                    "native": "ETH",
                    "max_per_tx": max_per_tx,
                    "max_per_day": max_per_day,
                    "max_gas_gwei": max_gas_gwei,
                    "allowed_contracts": {ok: "mint ok", bad: "revert"},
                }
            },
        )
        guard = Guard()
        wallet = EvmWallet(acct.key.hex(), guard)
        monkeypatch.setattr(wallet, "w3", lambda name: (guard.evm_chain(name), w3)[1])
        return wallet, guard

    return make, w3, ok, bad, stranger


def test_evm_mint_succeeds_and_is_recorded(evm):
    make, w3, ok, _, _ = evm
    wallet, guard = make()
    tx = wallet.send("local", ok, "0.001", MINT_DATA, "test mint")
    assert tx["status"] == "sukses"
    assert w3.eth.get_balance(ok) == w3.to_wei(Decimal("0.001"), "ether")
    spent = guard.spent_today("evm:local")
    assert Decimal("0.001") < spent < Decimal("0.0011")
    assert guard.ledger["history"][-1]["reason"] == "test mint"


def test_evm_rejects_non_allowlisted_address(evm):
    make, w3, _, _, stranger = evm
    wallet, _ = make()
    with pytest.raises(PolicyError, match="allowed_contracts"):
        wallet.send("local", stranger, "0.001", "0x", "kirim ke orang asing")
    assert w3.eth.get_balance(stranger) == 0


def test_evm_blocks_approve_even_on_allowed_contract(evm):
    make, _, ok, _, _ = evm
    wallet, _ = make()
    with pytest.raises(PolicyError, match="approve"):
        wallet.send("local", ok, "0", APPROVE_DATA, "approve")


def test_evm_per_tx_cap(evm):
    make, _, ok, _, _ = evm
    wallet, _ = make()
    with pytest.raises(PolicyError, match="per transaksi"):
        wallet.send("local", ok, "0.02", MINT_DATA, "kebesaran")


def test_evm_daily_cap(evm):
    make, _, ok, _, _ = evm
    wallet, _ = make()
    wallet.send("local", ok, "0.001", MINT_DATA, "1")
    wallet.send("local", ok, "0.006", MINT_DATA, "2")
    with pytest.raises(PolicyError, match="harian"):
        wallet.send("local", ok, "0.006", MINT_DATA, "3")


def test_evm_reverting_call_is_rejected_before_signing(evm):
    make, w3, _, bad, _ = evm
    wallet, guard = make()
    nonce = w3.eth.get_transaction_count(wallet.address)
    with pytest.raises(PolicyError, match="Simulasi gagal"):
        wallet.send("local", bad, "0", MINT_DATA, "revert")
    assert w3.eth.get_transaction_count(wallet.address) == nonce
    assert guard.spent_today("evm:local") == 0


def test_evm_gas_cap(evm):
    make, _, ok, _, _ = evm
    wallet, _ = make(max_gas_gwei=1)
    with pytest.raises(PolicyError, match="max_gas_gwei"):
        wallet.send("local", ok, "0.001", MINT_DATA, "gas mahal")


def test_evm_pause(evm):
    make, _, ok, _, _ = evm
    wallet, guard = make()
    guard.set_paused(True)
    with pytest.raises(PolicyError, match="pause"):
        wallet.send("local", ok, "0.001", MINT_DATA, "paused")


def test_evm_unknown_chain(evm):
    make, _, ok, _, _ = evm
    wallet, _ = make()
    with pytest.raises(PolicyError, match="tidak ada di policy"):
        wallet.send("mainnet", ok, "0.001", MINT_DATA, "chain lain")


# ---------------------------------------------------------------- Solana
SYSTEM = "11111111111111111111111111111111"
COMPUTE = "ComputeBudget111111111111111111111111111111"
TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
BLOCKHASH = Hash.default()


class FakeSolanaRpc:
    def __init__(self, owner: str, balance: int, spend: int):
        self.owner, self.balance, self.spend = owner, balance, spend
        self.sent = []

    def __call__(self, method, params):
        if method == "getBalance":
            return {"value": self.balance}
        if method == "getLatestBlockhash":
            return {"value": {"blockhash": str(BLOCKHASH)}}
        if method == "simulateTransaction":
            return {"value": {"err": None, "logs": [], "accounts": [{"lamports": self.balance - self.spend}]}}
        if method == "sendTransaction":
            self.sent.append(VersionedTransaction.from_bytes(base64.b64decode(params[0])))
            self.balance -= self.spend
            return "SIG123"
        if method == "getSignatureStatuses":
            return {"value": [{"confirmationStatus": "confirmed", "err": None}]}
        raise AssertionError(method)


@pytest.fixture
def sol(paths, monkeypatch):
    kp = Keypair()
    friend = Keypair().pubkey()

    def make(spend_lamports=1_000_000, programs=(SYSTEM, COMPUTE, TOKEN), per_tx="0.05", per_day="0.2"):
        write_policy(
            paths,
            solana={
                "rpc": "http://unused",
                "max_per_tx": per_tx,
                "max_per_day": per_day,
                "allowed_programs": {p: p for p in programs},
                "allowed_recipients": {str(friend): "teman"},
            },
        )
        guard = Guard()
        wallet = SolanaWallet(str(kp), guard)
        rpc = FakeSolanaRpc(str(kp.pubkey()), 10**9, spend_lamports)
        monkeypatch.setattr(wallet, "_rpc", rpc)
        monkeypatch.setattr("burner.solana.time.sleep", lambda s: None)
        return wallet, guard, rpc

    return make, kp, friend


def unsigned_tx(payer: Pubkey, ixs, extra_signer: Keypair | None = None) -> str:
    """Transaksi seperti dari API mint: signer lain sudah tanda tangan, slot burner kosong."""
    msg = MessageV0.try_compile(payer, ixs, [], BLOCKHASH)
    n = msg.header.num_required_signatures
    sigs = [Signature.default()] * n
    if extra_signer:
        keys = list(msg.account_keys)
        from solders.message import to_bytes_versioned

        sigs[keys.index(extra_signer.pubkey())] = extra_signer.sign_message(to_bytes_versioned(msg))
    return base64.b64encode(bytes(VersionedTransaction.populate(msg, sigs))).decode()


def test_sol_send_to_allowed_recipient(sol):
    make, kp, friend = sol
    wallet, guard, rpc = make()
    res = wallet.send_sol(str(friend), "0.001", "kirim ke teman")
    assert res["status"] == "sukses"
    assert all(rpc.sent[0].verify_with_results())
    assert guard.spent_today("solana") == Decimal("0.001")


def test_sol_send_to_stranger_rejected(sol):
    make, _, _ = sol
    wallet, _, rpc = make()
    with pytest.raises(PolicyError, match="allowed_recipients"):
        wallet.send_sol(str(Keypair().pubkey()), "0.001", "orang asing")
    assert not rpc.sent


def test_sol_sign_mint_tx_with_cosigner(sol):
    make, kp, _ = sol
    wallet, guard, rpc = make(spend_lamports=5_000_000)
    mint_authority = Keypair()
    ixs = [
        set_compute_unit_limit(200_000),
        transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=mint_authority.pubkey(), lamports=4_000_000)),
        Instruction(Pubkey.from_string(SYSTEM), bytes([0, 0, 0, 0]), [AccountMeta(mint_authority.pubkey(), True, True)]),
    ]
    res = wallet.sign_and_send(unsigned_tx(kp.pubkey(), ixs, extra_signer=mint_authority), "mint")
    assert res["status"] == "sukses"
    assert all(rpc.sent[0].verify_with_results()), "semua tanda tangan harus valid"
    assert guard.spent_today("solana") == Decimal("0.005")


def test_sol_unknown_program_rejected(sol):
    make, kp, _ = sol
    wallet, _, rpc = make()
    evil = Instruction(Keypair().pubkey(), b"\x01", [AccountMeta(kp.pubkey(), True, True)])
    with pytest.raises(PolicyError, match="allowed_programs"):
        wallet.sign_and_send(unsigned_tx(kp.pubkey(), [evil]), "program asing")
    assert not rpc.sent


def test_sol_token_approve_rejected(sol):
    make, kp, _ = sol
    wallet, _, rpc = make()
    approve = Instruction(
        Pubkey.from_string(TOKEN),
        bytes([4]) + (10**9).to_bytes(8, "little"),
        [AccountMeta(Keypair().pubkey(), False, True), AccountMeta(kp.pubkey(), True, False)],
    )
    with pytest.raises(PolicyError, match="Approve"):
        wallet.sign_and_send(unsigned_tx(kp.pubkey(), [approve]), "drainer")
    assert not rpc.sent


def test_sol_simulated_spend_over_cap_rejected(sol):
    make, kp, _ = sol
    wallet, _, rpc = make(spend_lamports=int(0.5 * 10**9))
    ix = transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=Keypair().pubkey(), lamports=1))
    with pytest.raises(PolicyError, match="per transaksi"):
        wallet.sign_and_send(unsigned_tx(kp.pubkey(), [ix]), "diam-diam nguras")
    assert not rpc.sent


def test_sol_not_a_signer_rejected(sol):
    make, _, _ = sol
    wallet, _, _ = make()
    other = Keypair()
    ix = transfer(TransferParams(from_pubkey=other.pubkey(), to_pubkey=Keypair().pubkey(), lamports=1))
    with pytest.raises(PolicyError, match="bukan signer"):
        wallet.sign_and_send(unsigned_tx(other.pubkey(), [ix]), "bukan punya kita")


def test_sol_missing_other_signature_rejected(sol):
    make, kp, _ = sol
    wallet, _, rpc = make()
    other = Keypair()
    ix = Instruction(Pubkey.from_string(SYSTEM), bytes([0, 0, 0, 0]), [AccountMeta(other.pubkey(), True, True)])
    with pytest.raises(PolicyError, match="butuh tanda tangan lain"):
        wallet.sign_and_send(unsigned_tx(kp.pubkey(), [ix]), "kurang signer")
    assert not rpc.sent


# ---------------------------------------------------------------- dispatcher
def test_run_tool_returns_rejection_text_not_exception(evm, monkeypatch, tmp_path):
    import burner.tools as tools

    make, _, ok, _, _ = evm
    wallet, guard = make()
    b = tools.Burner.__new__(tools.Burner)
    b.guard, b.evm, b.sol = guard, wallet, None
    monkeypatch.setattr(guard, "reload", lambda: None)  # policy sudah di-set fixture
    text, info = b.run_tool("burner_evm_send", {"chain": "local", "to": ok, "data": APPROVE_DATA, "reason": "x"})
    assert text.startswith("DITOLAK") and info["rejected"]
    text, info = b.run_tool("burner_evm_send", {"chain": "local", "to": ok, "value": "0.001", "data": MINT_DATA, "reason": "ok"})
    assert info["status"] == "sukses", text
