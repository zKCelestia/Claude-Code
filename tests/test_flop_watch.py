from flop import watch


def _fake(monkeypatch, spec=1014039, genesis=watch.GENESIS, best=1010, fin=1000,
          sentences=("Voucher earning starts at a future upgrade.",)):
    monkeypatch.setattr(watch, "chain_status", lambda: {
        "chain": "FLOP Testnet", "genesis": genesis, "genesis_ok": genesis == watch.GENESIS,
        "finalized": fin, "best": best, "finality_lag": best - fin,
        "spec_version": spec, "spec_name": "flop-testnet", "node_version": "1.1.0",
    })
    monkeypatch.setattr(watch, "faucet_status", lambda: {
        "genesis_ok": True, "status": "ok", "agent_grant": 10,
        "miner_sponsor": "automatic_full", "validator_sponsor": "automatic_full", "as_of": "x",
    })
    monkeypatch.setattr(watch, "page_sentences", lambda url: list(sentences))


def test_first_run_quiet(monkeypatch):
    _fake(monkeypatch)
    state, alerts, ok = watch.check({})
    assert ok and alerts == []
    assert state["chain"]["spec_version"] == 1014039


def test_runtime_upgrade_and_new_sentence(monkeypatch):
    _fake(monkeypatch)
    state, _, _ = watch.check({})
    _fake(monkeypatch, spec=1015000, sentences=(
        "Voucher earning starts at a future upgrade.",
        "Voucher earning starts at finalized block 300000.",
    ))
    _, alerts, ok = watch.check(state)
    assert ok
    assert any("Runtime upgrade" in a for a in alerts)
    assert any("block 300000" in a for a in alerts)
    assert sum("kalimat baru" in a for a in alerts) == len(watch.PAGES)  # satu per halaman


def test_genesis_mismatch_fails(monkeypatch):
    _fake(monkeypatch, genesis="0xdead")
    _, alerts, ok = watch.check({})
    assert not ok and any("GENESIS" in a for a in alerts)


def test_finality_lag_and_reset(monkeypatch):
    _fake(monkeypatch, best=5000, fin=1000)
    state, alerts, _ = watch.check({})
    assert any("Finality tertinggal" in a for a in alerts)
    _fake(monkeypatch, best=60, fin=50)
    _, alerts, _ = watch.check(state)
    assert any("reset" in a for a in alerts)
