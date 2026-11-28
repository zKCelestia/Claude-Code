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
