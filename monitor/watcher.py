"""Ambil postingan baru dari channel Telegram publik dan akun X, saring kata kunci,
lalu kembalikan alert. Tidak pernah mengklik link atau melakukan aksi apa pun.

- Telegram: halaman publik https://t.me/s/<channel> (tanpa login, gratis).
- X: API resmi v2 (butuh X_BEARER_TOKEN, paket berbayar). Tanpa token, X dilewati.

State (ID postingan terakhir per sumber) disimpan di monitor/state.json supaya
postingan lama tidak dikirim ulang. Saat sebuah sumber baru ditambahkan, postingan
yang sudah ada hanya dicatat (tidak dikirim), supaya tidak banjir alert.
"""

import html
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

log = logging.getLogger("monitor")
DIR = Path(__file__).resolve().parent
WATCHLIST = DIR / "watchlist.json"
EXAMPLE = DIR / "watchlist.example.json"
STATE = DIR / "state.json"
UA = {"User-Agent": "Mozilla/5.0 (airdrop-monitor)"}
NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,32}$")

# Pola yang sering dipakai scam/drainer. Hanya untuk memberi tanda waspada.
RISK_PATTERNS = [
    (r"connect (your )?wallet", "minta connect wallet"),
    (r"claim (now|here|your)", "ajakan claim langsung"),
    (r"seed phrase|private key|recovery phrase", "menyebut seed phrase/private key"),
    (r"(dm|message) (me|us)", "ajakan DM"),
    (r"limited (time|spots)|hurry|last chance|only \d+ (left|spots)", "bikin buru-buru"),
    (r"(send|deposit) .{0,20}(eth|sol|bnb|usdt|usdc)", "minta kirim/deposit koin"),
    (r"approve", "menyebut approve"),
]
LINK_SHORTENERS = {"bit.ly", "t.co", "tinyurl.com", "cutt.ly", "rb.gy", "is.gd", "shorturl.at", "linktr.ee"}


@dataclass
class Post:
    source: str  # "telegram" | "x"
    account: str
    post_id: str
    text: str
    url: str
    created_at: str


# ------------------------------------------------------------------ config/state
def load_watchlist() -> dict:
    path = WATCHLIST if WATCHLIST.exists() else EXAMPLE
    wl = json.loads(path.read_text())
    wl.setdefault("telegram", [])
    wl.setdefault("x", [])
    wl.setdefault("keywords", [])
    wl.setdefault("interval_minutes", 15)
    return wl


def save_watchlist(wl: dict) -> None:
    WATCHLIST.write_text(json.dumps(wl, indent=2, ensure_ascii=False))


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE)


def valid_name(name: str) -> bool:
    return bool(NAME_RE.match(name))


# ------------------------------------------------------------------ fetchers
def fetch_telegram(channel: str) -> list[Post]:
    r = requests.get(f"https://t.me/s/{channel}", headers=UA, timeout=30)
    r.raise_for_status()
    posts = []
    for block in re.findall(r'<div class="tgme_widget_message_wrap.*?(?=<div class="tgme_widget_message_wrap|\Z)', r.text, flags=re.S):
        pid = re.search(r'data-post="([^"]+)"', block)
        if not pid:
            continue
        body = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block, flags=re.S)
        ts = re.search(r'<time datetime="([^"]+)"', block)
        text = html.unescape(re.sub(r"<br\s*/?>", "\n", body.group(1))) if body else ""
        text = re.sub(r"<[^>]+>", "", text).strip()
        links = re.findall(r'<a[^>]+href="(https?://[^"]+)"', body.group(1)) if body else []
        if links:
            text += "\n" + "\n".join(dict.fromkeys(links))
        num = pid.group(1).split("/")[-1]
        posts.append(Post("telegram", channel, num, text, f"https://t.me/{pid.group(1)}", ts.group(1) if ts else ""))
    return posts


def fetch_x(username: str, token: str, state: dict) -> list[Post]:
    h = {"Authorization": f"Bearer {token}"}
    ids = state.setdefault("_x_user_ids", {})
    if username not in ids:
        r = requests.get(f"https://api.x.com/2/users/by/username/{username}", headers=h, timeout=30)
        r.raise_for_status()
        ids[username] = r.json()["data"]["id"]
    params = {"max_results": 10, "tweet.fields": "created_at,entities", "exclude": "replies"}
    last = state.get(f"x:{username}")
    if last:
        params["since_id"] = last
    r = requests.get(f"https://api.x.com/2/users/{ids[username]}/tweets", headers=h, params=params, timeout=30)
    r.raise_for_status()
    posts = []
    for t in r.json().get("data", []):
        text = t.get("text", "")
        urls = [u.get("expanded_url") for u in (t.get("entities") or {}).get("urls", []) if u.get("expanded_url")]
        if urls:
            text += "\n" + "\n".join(urls)
        posts.append(Post("x", username, t["id"], text, f"https://x.com/{username}/status/{t['id']}", t.get("created_at", "")))
    return posts


# ------------------------------------------------------------------ filtering
def matches(text: str, keywords: list[str]) -> list[str]:
    low = text.lower()
    return [k for k in keywords if k.lower() in low]


def risk_flags(text: str) -> list[str]:
    low = text.lower()
    flags = [label for pat, label in RISK_PATTERNS if re.search(pat, low)]
    for url in re.findall(r"https?://\S+", text):
        host = (urlparse(url).hostname or "").lower()
        if host in LINK_SHORTENERS:
            flags.append(f"link disingkat ({host})")
        if host.startswith("xn--") or ".xn--" in host:
            flags.append(f"domain punycode/mirip ({host})")
    return list(dict.fromkeys(flags))


def _newer(a: str, b: str | None) -> bool:
    if b is None:
        return True
    try:
        return int(a) > int(b)
    except ValueError:
        return a > b


# ------------------------------------------------------------------ main check
def check_once(x_token: str | None = None) -> tuple[list[dict], list[str]]:
    """Return (alerts, errors). Alert: post yang baru dan cocok kata kunci."""
    wl = load_watchlist()
    state = load_state()
    x_token = x_token if x_token is not None else os.environ.get("X_BEARER_TOKEN")
    alerts, errors = [], []

    sources = [("telegram", c) for c in wl["telegram"]]
    if x_token:
        sources += [("x", u) for u in wl["x"]]

    for kind, name in sources:
        if not valid_name(name):
            errors.append(f"{kind}:{name} nama tidak valid")
            continue
        key = f"{kind}:{name}"
        try:
            posts = fetch_telegram(name) if kind == "telegram" else fetch_x(name, x_token, state)
        except Exception as e:  # satu sumber gagal tidak menghentikan yang lain
            errors.append(f"{key}: {type(e).__name__}: {str(e)[:120]}")
            continue
        if not posts:
            continue
        last = state.get(key)
        first_time = last is None
        newest = last
        for p in posts:
            if not _newer(p.post_id, last):
                continue
            if _newer(p.post_id, newest):
                newest = p.post_id
            if first_time:
                continue  # sumber baru: catat saja, jangan banjiri alert
            hits = matches(p.text, wl["keywords"])
            if hits:
                alerts.append({"post": p.__dict__, "keywords": hits, "risks": risk_flags(p.text)})
        if newest is not None:
            state[key] = newest

    save_state(state)
    return alerts, errors


def format_alert(a: dict) -> str:
    p = a["post"]
    icon = "📣" if p["source"] == "telegram" else "🐦"
    text = p["text"].strip()
    if len(text) > 900:
        text = text[:900] + "…"
    lines = [f"{icon} {p['source'].upper()} @{p['account']} ({p['created_at'][:16].replace('T', ' ')})", "", text, ""]
    lines.append("Kata kunci: " + ", ".join(a["keywords"]))
    if a["risks"]:
        lines.append("⚠️ WASPADA: " + "; ".join(a["risks"]) + ". Jangan connect wallet utama, cek link resmi dulu.")
    lines.append(p["url"])
    return "\n".join(lines)
