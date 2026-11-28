"""Test klien zayro dengan relayer tiruan (tanpa jaringan).

Mengecek tanda tangan benar-benar bisa diverifikasi ke alamat yang tepat,
file kunci berizin 600, dan check-in selalu dicoba.
"""

import os
import stat

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

import zayro.client as zc
from zayro.client import Zayro, ZayroError, create_wallet


class Resp:
    def __init__(self, data, status=200):
        self._d, self.status_code, self.ok = data, status, status < 400

    def json(self):
        return self._d

    def raise_for_status(self):
        pass


class FakeRelayer:
    def __init__(self, missions=None, busy=0):
        self.posts = []
        self.missions = missions or []
        self.busy = busy

    def get(self, url, timeout=None):
        if "/missions/" in url:
            return Resp({"missions": self.missions})
        return Resp({"points": 0})

    def post(self, url, json=None, timeout=None):
        if self.busy:
            self.busy -= 1
            return Resp({"ok": False, "reason": "The exchange is busy right now"}, 503)
        self.posts.append((url.rsplit("/api-giwa", 1)[1], json))
        return Resp({"ok": True})


@pytest.fixture
def z(tmp_path, monkeypatch):
    monkeypatch.setattr(zc.time, "sleep", lambda s: None)
    p = tmp_path / ".env.zayro"
    create_wallet(p)
    return Zayro(path=p, http=FakeRelayer())


def test_wallet_file_private_and_not_overwritten(tmp_path):
    p = tmp_path / ".env.zayro"
    create_wallet(p)
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    with pytest.raises(ZayroError):
        create_wallet(p)


def test_session_key_registration_signed_by_wallet(z):
    z.register_session(nonce=0)
    route, body = z.http.posts[0]
    assert route == "/session-key" and body["user"] == z.address
    assert stat.S_IMODE(os.stat(z.path).st_mode) == 0o600
    # session key tersimpan dan bisa dipakai ulang tanpa registrasi baru
    assert Zayro(path=z.path, http=z.http)._session().address == body["sessionKey"]


def test_referral_signed_by_session_key(z):
    z.register_session(nonce=0)
    z.bind_referral(" 69961778 ")
    _, body = z.http.posts[-1]
    msg = f"zayro referral: {z.address.lower()} joins with code 69961778"
    assert body["code"] == "69961778"
    assert Account.recover_message(encode_defunct(text=msg), signature=body["signature"]) == body["sessionKey"]


def test_auto_missions_skip_x_and_review(z):
    z.register_session(nonce=0)
    z.http.missions = [
        {"id": "checkin", "claim": "checkin", "ready": False, "done": False},
        {"id": "post", "claim": "post", "x": True, "ready": True, "done": False},
        {"id": "bug", "claim": "review", "ready": True, "done": False},
        {"id": "username", "claim": "name", "ready": True, "done": False},
        {"id": "referred", "claim": "referred", "ready": True, "done": True},
    ]
    assert [m for m, _ in z.claim_auto_missions()] == ["checkin", "username"]


def test_busy_relayer_retried(z):
    z.http.busy = 2
    assert z.register_session(nonce=0)["ok"]


def test_autorun_binds_once_and_reports_only_work(z):
    z.http.missions = [{"id": "checkin", "claim": "checkin", "ready": False, "done": False}]
    first = z.autorun(ref="69961778")
    routes = [r for r, _ in z.http.posts]
    assert "/referral/bind" in routes and "/missions/claim" in routes
    assert any("referral" in line for line in first)
    z.http.missions = [{"id": "checkin", "claim": "checkin", "ready": False, "done": True}]
    n = len(z.http.posts)
    assert z.autorun(ref="69961778") == [] and len(z.http.posts) == n


def test_notify_sends_to_every_owner(monkeypatch):
    from zayro import notify

    sent = []

    class H:
        def post(self, url, json=None, timeout=None):
            sent.append((url, json["chat_id"]))
            return Resp({"ok": True})

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("ALLOWED_USER_IDS", "11, 22")
    assert notify.send("hai", http=H()) == []
    assert [c for _, c in sent] == ["11", "22"] and sent[0][0].endswith("/bot123:abc/sendMessage")


def test_notify_without_token_reports_error(monkeypatch):
    from zayro import notify

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert notify.send("hai") != []


def test_bug_report_validates_and_sends_note(z):
    z.register_session(nonce=0)
    with pytest.raises(ZayroError):
        z.report_bug("terlalu pendek")
    with pytest.raises(ZayroError):
        z.report_bug("x" * 30, url="javascript:alert(1)")
    z.report_bug("Tombol close  gagal\n saat harga lompat, ulangi: buka 1000x BTC", url="https://x.com/a/status/1")
    route, body = z.http.posts[-1]
    assert route == "/missions/claim" and body["mission"] == "bug"
    assert body["note"] == "Tombol close gagal saat harga lompat, ulangi: buka 1000x BTC"
    assert body["url"] == "https://x.com/a/status/1"


def test_spin_and_claim_are_signed_requests(z):
    z.register_session(nonce=0)
    z.spin()
    route, body = z.http.posts[-1]
    msg = f"zayro case: {z.address.lower()} at {body['at']}"
    assert route == "/cases"
    assert Account.recover_message(encode_defunct(text=msg), signature=body["signature"]) == body["sessionKey"]
    z.claim_prize(7, " 0xabc ", "https://x.com/me/status/1")
    route, body = z.http.posts[-1]
    assert route == "/cases/claim" and body["id"] == 7 and body["contact"] == "0xabc"


def test_inactive_session_key_is_reregistered(z):
    z.register_session(nonce=0)
    old = z.env["ZAYRO_SESSION_KEY"]
    replies = iter([{"ok": False, "reason": "session key is not active"}, {"ok": True}, {"ok": True}])
    real_post = z.http.post

    def post(url, json=None, timeout=None):
        if url.endswith("/missions/claim") or url.endswith("/session-key"):
            z.http.posts.append((url.rsplit("/api-giwa", 1)[1], json))
            return Resp(next(replies))
        return real_post(url, json=json, timeout=timeout)

    z.http.post = post
    z._nonce = lambda: 1
    assert z.claim_mission("checkin")["ok"]
    assert z.env["ZAYRO_SESSION_KEY"] != old
    assert [r for r, _ in z.http.posts[-3:]] == ["/missions/claim", "/session-key", "/missions/claim"]


# ---------------------------------------------------------------- on-chain
import json as _json

from eth_account.messages import encode_typed_data

import zayro.onchain as zo
from burner.policy import Guard, PolicyError


@pytest.fixture
def chain(z, tmp_path, monkeypatch):
    monkeypatch.setattr(zo, "POLICY_PATH", tmp_path / "zayro_policy.json")
    monkeypatch.setattr(zo, "LEDGER_PATH", tmp_path / "zayro_ledger.json")
    monkeypatch.setattr(zo, "STATE_PATH", tmp_path / ".zayro_state.json")
    z.register_session(nonce=0)
    return zo.ZayroChain(z, sleep=lambda s: None)


def test_zayro_policy_only_allows_swap_address(chain):
    g = chain.guard
    assert g.check_evm_call(zo.CHAIN, zo.SWAP_TO, "0x")
    with pytest.raises(PolicyError):
        g.check_evm_call(zo.CHAIN, "0x" + "11" * 20, "0x")
    approve = "0x095ea7b3" + "00" * 12 + "22" * 20 + "00" * 31 + "01"
    with pytest.raises(PolicyError):
        g.check_evm_call(zo.CHAIN, zo.SWAP_TO, approve)
    assert _json.loads(zo.POLICY_PATH.read_text())["evm"][zo.CHAIN]["max_per_day"] == "0.2"


def test_burner_guard_default_paths_unchanged():
    import burner.policy as bp

    assert Guard.__init__.__defaults__ == (None, None) and bp.POLICY_PATH.name == "burner_policy.json"


def test_open_and_close_intents_signed_by_session_key(chain):
    body = chain.open_intent(0, True, 10, 50)
    it = body["intent"]
    assert it["margin"] == "10000000" and it["leverage"] == 50 and it["isLong"] is True
    msg = {**it, "margin": int(it["margin"]), "limitPrice": 0, "deadline": int(it["deadline"]), "nonce": int(it["nonce"])}
    typed = {
        "types": {"EIP712Domain": zo.DOMAIN_TYPE, "OpenIntent": zo.OPEN_TYPE},
        "primaryType": "OpenIntent",
        "domain": {"name": "Zayro Orders", "version": "2", "chainId": zo.CHAIN_ID, "verifyingContract": zo.ORDERS},
        "message": msg,
    }
    signer = Account.recover_message(encode_typed_data(full_message=typed), signature=body["signature"])
    assert signer == chain.z.ensure_session().address
    close = chain.close_intent(42)["intent"]
    assert close["positionId"] == "42" and close["user"] == chain.z.address


def test_swap_refuses_when_swap_address_changes(chain, monkeypatch):
    monkeypatch.setattr(chain.z, "health", lambda: {"swap": {"open": True, "to": "0x" + "33" * 20, "rate": "10000"}})
    lines = chain.swap_available()
    assert lines and "berubah" in lines[0]


def test_trade_once_opens_waits_and_closes(chain, monkeypatch):
    monkeypatch.setattr(chain.z, "health", lambda: {"markets": [{"coin": "BTC", "instrumentId": 0, "retired": False, "opensPaused": False}]})
    accounts = iter([
        {"positions": [], "history": []},
        {"positions": [{"id": "7"}], "history": []},
        {"positions": [], "history": [{"id": "7", "pnl": "-1500000", "minted": str(150 * 10**18)}]},
    ])
    monkeypatch.setattr(chain, "account", lambda: next(accounts))
    lines = chain.trade_once()
    routes = [r for r, _ in chain.z.http.posts]
    assert "/open" in routes and "/close" in routes
    assert "PnL -1.50" in lines[0] and "+150 ZAYRO" in lines[0]


def test_trades_per_day_limit(chain, monkeypatch):
    calls = []
    monkeypatch.setattr(chain, "swap_available", lambda: [])
    monkeypatch.setattr(chain, "usdc_balance", lambda: 900)
    monkeypatch.setattr(chain, "trade_once", lambda: calls.append(1) or ["✓ trade"])
    monkeypatch.setenv("ZAYRO_TRADES_PER_DAY", "2")
    for _ in range(4):
        chain.autorun()
    assert len(calls) == 2
    monkeypatch.setenv("ZAYRO_TRADES_PER_DAY", "999")
    assert zo.trades_per_day() == 24
