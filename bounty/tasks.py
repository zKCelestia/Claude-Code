"""Papan tugas bug bounty: tugas dari Asa/Muse (#BOUNTY) yang menunggu /garap pemilik.

Format pesan tugas (satu pesan, baris "kunci: isi"):

    #BOUNTY
    program: acme
    target: https://api.acme.com/v2/users
    target: app.acme.com
    tes: cek IDOR/BOLA di endpoint user, bandingkan dua akun
    catatan: akun tes sudah ada di program page

`target` boleh diulang atau dipisah koma. `tes` = fokus pengujian.
Status tugas: menunggu -> jalan -> selesai/gagal/dihentikan, atau ditolak/batal.
"""

import json
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "bounty_tasks.json"
TAG = "#bounty"
MAX_PENDING = 20

_KEYS = {
    "program": "program",
    "target": "targets",
    "targets": "targets",
    "host": "targets",
    "tes": "focus",
    "test": "focus",
    "fokus": "focus",
    "focus": "focus",
    "catatan": "notes",
    "notes": "notes",
    "note": "notes",
}
_LINE_RE = re.compile(r"^\s*[-*]?\s*([A-Za-z]+)\s*[:=]\s*(.+?)\s*$")


def has_tag(text: str) -> bool:
    return TAG in (text or "").lower()


def parse_task(text: str) -> dict:
    """Ambil program/target/fokus/catatan dari pesan #BOUNTY. Raise ValueError kalau kurang."""
    out: dict = {"program": "", "targets": [], "focus": "", "notes": ""}
    for line in (text or "").splitlines():
        m = _LINE_RE.match(line)
        if not m:
            continue
        key = _KEYS.get(m.group(1).lower())
        if not key:
            continue
        val = m.group(2)
        if key == "targets":
            out["targets"] += [v.strip() for v in val.split(",") if v.strip()]
        elif key == "program":
            out["program"] = val.strip()
        else:
            out[key] = (out[key] + "\n" + val).strip() if out[key] else val
    missing = [k for k in ("program", "targets", "focus") if not out[k]]
    if missing:
        raise ValueError("kurang: " + ", ".join({"targets": "target", "focus": "tes"}.get(k, k) for k in missing))
    out["focus"] = out["focus"][:1500]
    out["notes"] = out["notes"][:1500]
    return out


@dataclass
class Task:
    id: str
    program: str
    hosts: list[str]
    targets: list[str]
    focus: str
    notes: str
    source: str  # nama pengirim
    source_is_bot: bool
    chat_id: int
    status: str = "menunggu"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    session_id: str | None = None
    result: str = ""


class TaskBoard:
    def __init__(self, path: Path = TASKS_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        data = json.loads(path.read_text()) if path.exists() else {}
        self.next_no: int = data.get("next", 1)
        self.tasks: dict[str, Task] = {k: Task(**v) for k, v in (data.get("tasks") or {}).items()}
        self.envs: dict[str, str] = data.get("envs") or {}  # "host1,host2" -> environment_id
        # Tugas yang "jalan" saat bot mati tidak akan dilanjutkan.
        for t in self.tasks.values():
            if t.status == "jalan":
                t.status, t.result = "gagal", "bot restart saat tugas berjalan"

    def save(self) -> None:
        with self._lock:
            data = {
                "next": self.next_no,
                "tasks": {k: asdict(v) for k, v in self.tasks.items()},
                "envs": self.envs,
            }
            self.path.write_text(json.dumps(data, indent=2))

    def add(self, **kw) -> Task:
        pending = [t for t in self.tasks.values() if t.status == "menunggu"]
        if len(pending) >= MAX_PENDING:
            raise ValueError(f"sudah ada {MAX_PENDING} tugas menunggu; /tolak dulu sebagian")
        task = Task(id=f"B{self.next_no}", **kw)
        self.next_no += 1
        self.tasks[task.id] = task
        self.save()
        return task

    def get(self, task_id: str) -> Task | None:
        return self.tasks.get((task_id or "").strip().upper())

    def running(self) -> list[Task]:
        return [t for t in self.tasks.values() if t.status == "jalan"]

    def started_last_24h(self) -> int:
        now = time.time()
        return sum(1 for t in self.tasks.values() if t.started_at and now - t.started_at < 86400)

    def recent(self, n: int = 10) -> list[Task]:
        return sorted(self.tasks.values(), key=lambda t: -t.created_at)[:n]
