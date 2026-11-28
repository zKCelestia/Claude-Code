"""Test helper garapan Gama di GIWA Sepolia (tanpa jaringan)."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from web3 import Web3

import burner.policy as policy_mod
from burner.giwa import (
    BUY_SELECTOR,
    GAMA_LAUNCHPAD,
    GIWA_OPTIMISM_PORTAL,
    L1_CHAIN,
    L2_CHAIN,
    buy_calldata,
    min_out_with_slippage,
)
from burner.policy import BLOCKED_EVM_SELECTORS, Guard, PolicyError

TOKEN = "0x66ae12790aaac660a907fb1278dfbc58027a3894"
EXAMPLE = Path(__file__).resolve().parent.parent / "burner" / "policy.example.json"


def test_buy_calldata_matches_abi_encoding():
    abi = [
        {
            "type": "function",
            "name": "buy",
            "stateMutability": "payable",
            "inputs": [{"type": "address", "name": "token"}, {"type": "uint256", "name": "minTokensOut"}],
            "outputs": [{"type": "uint256"}],
        }
    ]
    c = Web3().eth.contract(address=GAMA_LAUNCHPAD, abi=abi)
    expected = c.encode_abi("buy", [Web3.to_checksum_address(TOKEN), 12345])
    assert buy_calldata(TOKEN, 12345) == expected
    assert expected.startswith(BUY_SELECTOR)
    assert BUY_SELECTOR not in BLOCKED_EVM_SELECTORS


def test_buy_calldata_rejects_bad_input():
    with pytest.raises(PolicyError):
        buy_calldata("0x123", 1)
    with pytest.raises(PolicyError):
        buy_calldata(TOKEN, -1)


def test_slippage():
    assert min_out_with_slippage(1000, Decimal("10")) == 900
    assert min_out_with_slippage(1000, Decimal("0")) == 1000
    with pytest.raises(PolicyError):
        min_out_with_slippage(1000, Decimal("100"))


@pytest.fixture
def example_guard(tmp_path, monkeypatch):
    pol = json.loads(EXAMPLE.read_text())
    (tmp_path / "burner_policy.json").write_text(json.dumps(pol))
    monkeypatch.setattr(policy_mod, "POLICY_PATH", tmp_path / "burner_policy.json")
    monkeypatch.setattr(policy_mod, "LEDGER_PATH", tmp_path / "burner_ledger.json")
    return Guard()


def test_example_policy_allows_gama_flow(example_guard):
    g = example_guard
    assert g.evm_chain(L1_CHAIN)["chain_id"] == 11155111
    assert g.evm_chain(L2_CHAIN)["chain_id"] == 91342
    assert "OptimismPortal" in g.check_evm_call(L1_CHAIN, GIWA_OPTIMISM_PORTAL, "0x")
    assert "GamaLaunchpad" in g.check_evm_call(L2_CHAIN, GAMA_LAUNCHPAD, buy_calldata(TOKEN, 1))


def test_example_policy_still_blocks_drainers(example_guard):
    g = example_guard
    with pytest.raises(PolicyError):
        g.check_evm_call(L2_CHAIN, TOKEN, "0x")  # token tile tidak di allowlist
    with pytest.raises(PolicyError):
        g.check_evm_call(L2_CHAIN, GAMA_LAUNCHPAD, "0x095ea7b3" + "00" * 64)  # approve
    with pytest.raises(PolicyError):
        g.check_evm_call(L1_CHAIN, GAMA_LAUNCHPAD, "0x")  # salah chain
