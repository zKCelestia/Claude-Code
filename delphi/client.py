"""Klien kecil untuk Delphi Agent Competition (evidence mining).

Key dibaca dari DELPHI_API_ACCESS_KEY. Di sesi Claude Code cloud, key disuntikkan oleh
proxy, jadi variabel cukup diisi placeholder (`proxy-injected`).

Pemakaian:
  python -m delphi.client limits
  python -m delphi.client markets                 # pasar + slot tersisa + pot
  python -m delphi.client mine [--market 0x..]    # submission akun ini
  python -m delphi.client submit --market 0x.. --note-file note.txt --link URL [--link URL]
  python -m delphi.client result <submission_id>

Pengaman bawaan pada `submit`:
- cek entry-state (canSubmit) dulu,
- tolak kalau akun sudah punya submission untuk pasar itu yang belum ditolak sebagai duplicate,
- tolak kalau link yang sama sudah pernah dikirim akun ini ke pasar itu,
- maksimal 3 item (note + link),
- Idempotency-Key unik per submission,
- semua dicatat ke delphi/submissions.jsonl.
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://delphi.fyi/v1"
MARKETS_URL = "https://competition.delphi.fyi/markets.json"
LOG = Path(__file__).with_name("submissions.jsonl")
AGENT_HEADERS = {
    "X-Agent-Id": "claude-code-delphi",
    "X-Agent-Harness": "claude-code",
    "X-Agent-Model": os.environ.get("DELPHI_AGENT_MODEL", "claude-opus-5-5"),
}


def _headers() -> dict:
    key = os.environ.get("DELPHI_API_ACCESS_KEY") or "proxy-injected"
    return {"Authorization": f"Bearer {key}", **AGENT_HEADERS}


def api(method: str, path: str, **kw):
    r = requests.request(method, BASE + path, headers={**_headers(), **kw.pop("headers", {})}, timeout=60, **kw)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text[:500]}
    return r.status_code, body, r.headers


def log(entry: dict) -> None:
    entry = {"time": datetime.now(timezone.utc).isoformat(), **entry}
    with LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def competition_markets() -> list[dict]:
    r = requests.get(MARKETS_URL, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("markets", data) if isinstance(data, dict) else data


def my_submissions(market: str | None = None) -> list[dict]:
    items, cursor = [], None
    while True:
        params = {"limit": 100}
        if market:
            params["market"] = market
        if cursor:
            params["cursor"] = cursor
        status, body, _ = api("GET", "/submissions", params=params)
        if status != 200:
            raise SystemExit(f"Gagal list submissions: {status} {body}")
        items += body.get("items", [])
        cursor = body.get("nextCursor")
        if not cursor:
            return items


def entry_state(market: str) -> dict:
    _, body, _ = api("GET", f"/markets/{market}/entry-state")
    return body


DUPLICATE_REFUNDS_PER_DAY = 10  # duplicate dikembalikan slotnya maks 10x per 24 jam per akun


def duplicates_last_24h(items: list[dict] | None = None) -> int:
    items = my_submissions() if items is None else items
    now = datetime.now(timezone.utc)
    n = 0
    for s in items:
        created = datetime.fromisoformat(s.get("createdAt", "1970-01-01T00:00:00+00:00").replace("Z", "+00:00"))
        if (now - created).total_seconds() < 86400 and any(m.get("verdict") == "duplicate" for m in s.get("markets", [])):
            n += 1
    return n


def check_before_submit(market: str, links: list[str]) -> None:
    dups = duplicates_last_24h()
    if dups >= DUPLICATE_REFUNDS_PER_DAY and os.environ.get("DELPHI_ALLOW_NO_REFUND") != "1":
        raise SystemExit(
            f"Akun sudah kena {dups} duplicate dalam 24 jam: pengembalian slot habis, jadi duplicate berikutnya "
            "menghanguskan slot pasar. Set DELPHI_ALLOW_NO_REFUND=1 hanya untuk bukti yang sangat yakin baru."
        )
    es = entry_state(market)
    if not es.get("canSubmit"):
        raise SystemExit(f"Tidak bisa submit ke {market}: {es.get('reason')} ({es})")
    for s in my_submissions(market):
        lines = [m for m in s.get("markets", []) if m.get("marketAddress", "").lower() == market.lower()]
        live = [m for m in lines if m.get("verdict") != "duplicate" and m.get("status") != "not_accepted"]
        if live:
            raise SystemExit(f"Akun ini sudah punya submission aktif di pasar ini ({s.get('id')}, agent {s.get('agentId')}).")
        sent = set(s.get("links") or [])
        dup = sent.intersection(links)
        if dup:
            raise SystemExit(f"Link ini sudah pernah dikirim akun ini ke pasar ini: {', '.join(dup)}")


def submit(market: str, note: str, links: list[str], files: list[str] | None = None) -> dict:
    files = files or []
    if 1 + len(links) + len(files) > 3:
        raise SystemExit("Maksimal 3 item per submission (note + link + file).")
    if len(note) > 8000:
        raise SystemExit(f"Note terlalu panjang ({len(note)} > 8000 karakter).")
    check_before_submit(market, links)
    fields = [("marketAddress", (None, market)), ("note", (None, note))]
    fields += [("links[]", (None, url)) for url in links]
    for path in files:
        mime = "text/csv" if path.endswith(".csv") else "application/pdf" if path.endswith(".pdf") else "text/plain"
        fields.append(("files", (Path(path).name, Path(path).read_bytes(), mime)))
    status, body, hdrs = api("POST", "/submissions", files=fields, headers={"Idempotency-Key": str(uuid.uuid4())})
    log({"event": "submit", "market": market, "status": status, "response": body, "links": links, "files": files, "note": note})
    return {"http": status, **body, "retryAfter": hdrs.get("Retry-After")}


def wait_result(sub_id: str, max_seconds: int = 1800) -> dict:
    deadline = time.monotonic() + max_seconds
    while True:
        status, body, hdrs = api("GET", f"/submissions/{sub_id}")
        if body.get("status") not in ("queued", "judging") or time.monotonic() > deadline:
            log({"event": "result", "id": sub_id, "response": body})
            return body
        time.sleep(min(60, int(hdrs.get("Retry-After") or 20)))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("limits")
    sub.add_parser("markets")
    m = sub.add_parser("mine")
    m.add_argument("--market")
    s = sub.add_parser("submit")
    s.add_argument("--market", required=True)
    s.add_argument("--note-file", required=True)
    s.add_argument("--link", action="append", default=[])
    s.add_argument("--file", action="append", default=[])
    s.add_argument("--no-wait", action="store_true")
    r = sub.add_parser("result")
    r.add_argument("id")
    a = p.parse_args()

    if a.cmd == "limits":
        print(json.dumps(api("GET", "/limits")[1], indent=2))
    elif a.cmd == "markets":
        for mk in sorted(competition_markets(), key=lambda x: x.get("evidenceCutoffAt", "")):
            es = entry_state(mk["address"])
            pot = int(es.get("judgementPotRemainingBaseUnits") or 0) / 1e6
            flag = "OK" if es.get("canSubmit") else (es.get("reason") or "--")
            yes = (mk.get("odds") or {}).get("yes")
            print(f"{flag:13} cutoff={mk['evidenceCutoffAt'][:16]} pot=${pot:5.2f} yes={yes:.0%} {mk['address']} | {mk['question'][:90]}")
            time.sleep(0.3)
    elif a.cmd == "mine":
        for s_ in my_submissions(a.market):
            lines = [(x.get("marketAddress", "")[:10], x.get("status"), x.get("verdict"), (x.get("bounty") or {}).get("amount")) for x in s_.get("markets", [])]
            print(s_.get("createdAt"), s_.get("agentId"), s_.get("status"), lines)
    elif a.cmd == "submit":
        note = Path(a.note_file).read_text().strip()
        res = submit(a.market, note, a.link, a.file)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        if res.get("id") and res.get("http") == 202 and not a.no_wait:
            print(json.dumps(wait_result(res["id"]), indent=2, ensure_ascii=False))
    elif a.cmd == "result":
        print(json.dumps(wait_result(a.id, max_seconds=0), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
