"""Guard scope bug bounty: target hanya boleh digarap kalau ada di scope resmi program.

Scope diisi pemilik sendiri di bounty_scope.json (salin dari bounty/scope.example.json),
disalin dari halaman program (HackerOne, Bugcrowd, Intigriti, Immunefi, VDP, dll.).
Pesan dari bot lain (mis. Asa/Muse) tidak bisa menambah scope.

Aturan pencocokan:
- "api.acme.com"  : host itu persis.
- "*.acme.com"    : semua subdomain acme.com, TIDAK termasuk acme.com sendiri
                    (tulis "acme.com" terpisah kalau apex juga in-scope).
- out_of_scope selalu menang atas in_scope.
- Alamat IP ditolak (environment sandbox hanya menerima nama host).
"""

import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SCOPE_PATH = ROOT / "bounty_scope.json"
MAX_HOSTS_PER_TASK = 10

_HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$")


class ScopeError(Exception):
    pass


def normalize_host(target: str) -> str:
    """Ambil host dari URL/host mentah dan validasi. Raise ScopeError kalau aneh."""
    raw = (target or "").strip().strip("<>").strip()
    if not raw:
        raise ScopeError("target kosong")
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    if parts.scheme not in ("http", "https"):
        raise ScopeError(f"skema {parts.scheme!r} tidak didukung (hanya http/https)")
    if parts.username or parts.password or "@" in parts.netloc:
        raise ScopeError("URL berisi userinfo (@), ditolak")
    host = (parts.hostname or "").rstrip(".").lower()
    try:
        ipaddress.ip_address(host)
        raise ScopeError(f"{host} adalah alamat IP; pakai nama host")
    except ValueError:
        pass
    if not _HOST_RE.match(host):
        raise ScopeError(f"host {host!r} tidak valid")
    return host


def _pattern(entry: str) -> str:
    entry = entry.strip().lower()
    if entry.startswith("*."):
        return "*." + normalize_host(entry[2:])
    return normalize_host(entry)


def host_matches(host: str, pattern: str) -> bool:
    if pattern.startswith("*."):
        return host.endswith(pattern[1:])  # ".acme.com"
    return host == pattern


class Scope:
    def __init__(self, data: dict) -> None:
        self.programs: dict[str, dict] = {}
        for key, prog in (data.get("programs") or {}).items():
            if key.startswith("_"):
                continue
            prog = dict(prog)
            prog["in_scope"] = [_pattern(p) for p in prog.get("in_scope", [])]
            prog["out_of_scope"] = [_pattern(p) for p in prog.get("out_of_scope", [])]
            self.programs[key.strip().lower()] = prog

    @classmethod
    def load(cls, path: Path = SCOPE_PATH) -> "Scope":
        if not path.exists():
            raise ScopeError(
                f"{path.name} belum ada. Salin bounty/scope.example.json ke {path.name} "
                "lalu isi scope resmi programnya."
            )
        return cls(json.loads(path.read_text()))

    def program(self, name: str) -> dict:
        prog = self.programs.get((name or "").strip().lower())
        if prog is None:
            known = ", ".join(sorted(self.programs)) or "(kosong)"
            raise ScopeError(f"program {name!r} tidak ada di bounty_scope.json. Yang terdaftar: {known}")
        if prog.get("active", True) is False:
            raise ScopeError(f"program {name!r} sedang dinonaktifkan (active: false)")
        return prog

    def check(self, program: str, targets: list[str]) -> list[str]:
        """Kembalikan daftar host unik yang lolos. Raise ScopeError kalau ada satu pun yang gagal."""
        prog = self.program(program)
        if not targets:
            raise ScopeError("tidak ada target")
        hosts: list[str] = []
        for t in targets:
            host = normalize_host(t)
            if any(host_matches(host, p) for p in prog["out_of_scope"]):
                raise ScopeError(f"{host} termasuk OUT-OF-SCOPE program {program}")
            if not any(host_matches(host, p) for p in prog["in_scope"]):
                raise ScopeError(f"{host} tidak ada di in-scope program {program}")
            if host not in hosts:
                hosts.append(host)
        if len(hosts) > MAX_HOSTS_PER_TASK:
            raise ScopeError(f"maksimal {MAX_HOSTS_PER_TASK} host per tugas (ada {len(hosts)})")
        return hosts
