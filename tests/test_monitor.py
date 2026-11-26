"""Test pemantau airdrop: sumber baru tidak banjir, alert hanya untuk post baru yang cocok,
tidak dobel, X dilewati tanpa token, dan tanda waspada scam."""

import monitor.watcher as w
from monitor.watcher import Post


def setup(tmp_path, monkeypatch, posts_by_channel, keywords=("airdrop",)):
    monkeypatch.setattr(w, "WATCHLIST", tmp_path / "watchlist.json")
    monkeypatch.setattr(w, "STATE", tmp_path / "state.json")
    w.save_watchlist({"interval_minutes": 15, "telegram": list(posts_by_channel), "x": ["akunx"], "keywords": list(keywords)})
    monkeypatch.setattr(w, "fetch_telegram", lambda ch: posts_by_channel[ch])

    def no_x(*a, **k):
        raise AssertionError("X tidak boleh dipanggil tanpa token")

    monkeypatch.setattr(w, "fetch_x", no_x)


def post(ch, i, text):
    return Post("telegram", ch, str(i), text, f"https://t.me/{ch}/{i}", "2026-11-26T08:00:00+00:00")


def test_new_source_does_not_flood_then_alerts_on_new_matching_post(tmp_path, monkeypatch):
    feed = {"proj": [post("proj", 1, "Airdrop season 1 live"), post("proj", 2, "gm")]}
    setup(tmp_path, monkeypatch, feed)
    alerts, errors = w.check_once(x_token="")
    assert alerts == [] and errors == []

    feed["proj"] += [post("proj", 3, "Snapshot for the AIRDROP is tomorrow"), post("proj", 4, "gm again")]
    alerts, _ = w.check_once(x_token="")
    assert [a["post"]["post_id"] for a in alerts] == ["3"]
    assert alerts[0]["keywords"] == ["airdrop"]

    alerts, _ = w.check_once(x_token="")
    assert alerts == [], "post yang sama tidak dikirim dua kali"


def test_one_broken_source_does_not_stop_others(tmp_path, monkeypatch):
    feed = {"ok": [post("ok", 1, "x")]}
    setup(tmp_path, monkeypatch, feed)
    w.save_watchlist({"interval_minutes": 15, "telegram": ["ok", "rusak"], "x": [], "keywords": ["airdrop"]})

    def fetch(ch):
        if ch == "rusak":
            raise RuntimeError("404")
        return feed[ch]

    monkeypatch.setattr(w, "fetch_telegram", fetch)
    w.check_once(x_token="")
    feed["ok"].append(post("ok", 2, "airdrop claim"))
    alerts, errors = w.check_once(x_token="")
    assert len(alerts) == 1 and any("rusak" in e for e in errors)


def test_invalid_names_are_rejected(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, {})
    w.save_watchlist({"interval_minutes": 15, "telegram": ["../etc", "ok_name"], "x": [], "keywords": []})
    monkeypatch.setattr(w, "fetch_telegram", lambda ch: [])
    _, errors = w.check_once(x_token="")
    assert any("../etc" in e for e in errors)


def test_risk_flags():
    flags = w.risk_flags("Claim now! Connect your wallet: https://bit.ly/x https://xn--uniswp-9za.org send 0.1 ETH")
    joined = " ".join(flags)
    assert "connect wallet" in joined and "claim" in joined and "bit.ly" in joined and "punycode" in joined
    assert "kirim/deposit" in joined
    assert w.risk_flags("Testnet season 2 is live, read the docs at https://docs.project.xyz") == []


def test_alert_format_has_warning_and_link():
    a = {"post": post("proj", 9, "Claim now, connect wallet").__dict__, "keywords": ["claim"], "risks": ["minta connect wallet"]}
    text = w.format_alert(a)
    assert "WASPADA" in text and "https://t.me/proj/9" in text
