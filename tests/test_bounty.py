"""Test mode bug bounty: guard scope, parser #BOUNTY, papan tugas, dan prompt runner."""

import json

import pytest

from bounty import runner
from bounty.scope import Scope, ScopeError, normalize_host
from bounty.tasks import TaskBoard, has_tag, parse_task

SCOPE = Scope(
    {
        "programs": {
            "_contoh": {"in_scope": ["x.com"]},
            "Acme": {
                "platform": "hackerone",
                "in_scope": ["acme.com", "*.acme.com", "https://api.acme.io/"],
                "out_of_scope": ["blog.acme.com", "*.internal.acme.com"],
                "max_rps": 3,
                "rules": "no dos",
            },
            "mati": {"active": False, "in_scope": ["mati.com"]},
        }
    }
)


@pytest.mark.parametrize(
    "target,host",
    [
        ("https://API.acme.com/v1/users?id=1", "api.acme.com"),
        ("app.acme.com:8443/login", "app.acme.com"),
        ("acme.com.", "acme.com"),
    ],
)
def test_normalize_host(target, host):
    assert normalize_host(target) == host


@pytest.mark.parametrize(
    "target",
    ["", "ftp://acme.com", "https://acme.com@evil.com/", "http://10.0.0.1/", "https://[::1]/", "localhost", "a_b.acme.com"],
)
def test_normalize_host_rejects(target):
    with pytest.raises(ScopeError):
        normalize_host(target)


def test_in_scope_hosts_pass_and_dedupe():
    hosts = SCOPE.check("acme", ["https://acme.com", "api.acme.com/x", "https://api.acme.com/y", "api.acme.io"])
    assert hosts == ["acme.com", "api.acme.com", "api.acme.io"]


@pytest.mark.parametrize(
    "target",
    [
        "evilacme.com",  # bukan subdomain
        "acme.com.evil.com",
        "blog.acme.com",  # out-of-scope eksplisit
        "db.internal.acme.com",  # out-of-scope wildcard
        "x.api.acme.io",  # host persis tidak mencakup subdomain
        "https://acme.com@evil.com",
    ],
)
def test_out_of_scope_rejected(target):
    with pytest.raises(ScopeError):
        SCOPE.check("acme", [target])


def test_one_bad_target_rejects_whole_task():
    with pytest.raises(ScopeError):
        SCOPE.check("acme", ["api.acme.com", "evil.com"])


def test_unknown_inactive_and_placeholder_programs():
    for name in ("nggak-ada", "mati", "_contoh"):
        with pytest.raises(ScopeError):
            SCOPE.check(name, ["mati.com"])


def test_max_hosts_per_task():
    with pytest.raises(ScopeError):
        SCOPE.check("acme", [f"h{i}.acme.com" for i in range(11)])


def test_missing_scope_file(tmp_path):
    with pytest.raises(ScopeError):
        Scope.load(tmp_path / "bounty_scope.json")


MSG = """Bos, ada kandidat nih
#BOUNTY
program: Acme
target: https://api.acme.com/v2/users, app.acme.com
- target: acme.com
tes: cek IDOR di /v2/users/{id}
catatan: pakai 2 akun tes
"""


def test_parse_task():
    assert has_tag(MSG) and not has_tag("bounty biasa")
    t = parse_task(MSG)
    assert t["program"] == "Acme"
    assert t["targets"] == ["https://api.acme.com/v2/users", "app.acme.com", "acme.com"]
    assert t["focus"] == "cek IDOR di /v2/users/{id}"
    assert t["notes"] == "pakai 2 akun tes"


def test_parse_task_missing_fields():
    with pytest.raises(ValueError, match="target"):
        parse_task("#BOUNTY\nprogram: acme\ntes: xss")


def _add(board, **kw):
    base = dict(program="acme", hosts=["api.acme.com"], targets=["api.acme.com"], focus="idor", notes="",
                source="Asa", source_is_bot=True, chat_id=-100)
    base.update(kw)
    return board.add(**base)


def test_board_persists_and_marks_interrupted_runs_failed(tmp_path):
    path = tmp_path / "bounty_tasks.json"
    board = TaskBoard(path)
    a, b = _add(board), _add(board)
    assert (a.id, b.id) == ("B1", "B2")
    b.status = "jalan"
    board.envs["api.acme.com"] = "env_1"
    board.save()

    again = TaskBoard(path)
    assert again.get("b1").status == "menunggu"
    assert again.get("B2").status == "gagal"
    assert again.envs == {"api.acme.com": "env_1"}
    assert _add(again).id == "B3"
    assert json.loads(path.read_text())["next"] == 4


def test_board_caps_pending(tmp_path):
    board = TaskBoard(tmp_path / "t.json")
    for _ in range(20):
        _add(board)
    with pytest.raises(ValueError):
        _add(board)


class FakeEnvs:
    def __init__(self):
        self.created = []

    def create(self, **kw):
        self.created.append(kw)
        return type("Env", (), {"id": f"env_{len(self.created)}"})()


def test_environment_locked_to_task_hosts_and_reused(tmp_path):
    envs = FakeEnvs()
    client = type("C", (), {"beta": type("B", (), {"environments": envs})()})()
    board = TaskBoard(tmp_path / "t.json")
    e1 = runner.environment_for(client, board, ["b.acme.com", "a.acme.com"])
    e2 = runner.environment_for(client, board, ["a.acme.com", "b.acme.com"])
    assert e1 == e2 == "env_1" and len(envs.created) == 1
    net = envs.created[0]["config"]["networking"]
    assert net["type"] == "limited"
    assert net["allowed_hosts"] == ["a.acme.com", "b.acme.com"]
    assert net["allow_mcp_servers"] is False


def test_budget_and_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("BOUNTY_BUDGET_USD", "2.5")
    assert runner.budget_cents() == "250"
    board = TaskBoard(tmp_path / "t.json")
    task = _add(board, focus="cek IDOR")
    prompt = runner.build_prompt(task, SCOPE.program("acme"))
    assert "api.acme.com" in prompt and "maksimal 3 request/detik" in prompt
    assert "laporan_B1.md" in prompt and "no dos" in prompt
