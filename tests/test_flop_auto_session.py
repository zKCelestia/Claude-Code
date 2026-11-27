import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "flop"))
import auto_session as a  # noqa: E402

ME = "5FbXs9twtnVtSTweiFiYW3phbBTmZKnR1azMG77WjUhhyCx1"
H8 = "0xaaa"
MODELS = {H8: "qwen/qwen3-8b"}


def row(miner="5Miner", escrow=5 * 10**15, venue="https://m.example", verified=False, settled=0,
        model=H8, expiry=10_000, blacklisted=False):
    return {"offer": {"miner": miner, "modelHash": model, "minEscrow": str(escrow), "expiry": expiry},
            "venue": venue, "venueVerified": verified,
            "onChainFacts": {"active": True, "blacklisted": blacklisted, "reliability": {"settledCount": settled}}}


def test_skips_self_expensive_unknown_model_and_blacklisted():
    rows = [row(miner=ME), row(escrow=2 * 10**16), row(model="0xbbb"), row(blacklisted=True), row(expiry=5)]
    cand, why = a.choose(rows, MODELS, ME, block=100)
    assert cand is None and "belum ada offer" in why


def test_reports_missing_venue():
    cand, why = a.choose([row(venue=None)], MODELS, ME, block=100)
    assert cand is None and "endpoint" in why


def test_prefers_verified_then_settled_then_cheapest():
    rows = [row(miner="A", settled=50, escrow=10**15),
            row(miner="B", verified=True, settled=1, escrow=9 * 10**15),
            row(miner="C", verified=True, settled=9, escrow=9 * 10**15, venue={"url": "https://c.example/"})]
    cand, _ = a.choose(rows, MODELS, ME, block=100)
    assert cand["miner"] == "C" and cand["endpoint"] == "https://c.example"


def test_brakes(monkeypatch):
    monkeypatch.setattr(a, "now", lambda: 1_000_000.0)
    assert a.brakes({"sessions": []}, Decimal("10")) == ""
    assert "24 jam" in a.brakes({"sessions": [{"ts": 1_000_000 - 3600, "escrow": "0.01"}]}, Decimal("10"))
    week = [{"ts": 1_000_000 - d * 86400 - 10, "escrow": "0.01"} for d in range(1, 6)]
    assert "7 hari" in a.brakes({"sessions": week}, Decimal("10"))
    assert "saldo" in a.brakes({"sessions": []}, Decimal("0.2"))
