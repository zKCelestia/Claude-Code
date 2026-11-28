#!/usr/bin/env python3
"""Scout: list make.fun bounties opened since the last scout, with what each needs.

Step 1 of the make.fun workflow. Prints every open bounty published after the time stored in
~/.makefun/scout-state.json (or the last --hours hours on a first run), largest reward first, with
its deadline, harness, entry fee, the account's quota and flags: SOCIAL when it asks to post on X or
another social network (bos decides those), FREEBUFF when only Freebuff may build it (bos builds it
on his VPS, Liz directs), FEE when it costs to enter. Then stores the newest time it saw.

Usage: python3 makefun/tools/scout.py [--hours 6] [--min-reward 0] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import re
import urllib.request

ORIGIN = "https://make.fun"
STATE = os.path.expanduser("~/.makefun/scout-state.json")


def key():
    with open(os.path.expanduser("~/.makefun/credentials"), encoding="utf8") as f:
        return json.load(f)["keys"][ORIGIN]["key"]


def get(path):
    req = urllib.request.Request(ORIGIN + path, headers={"x-api-key": key()})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    return body.get("data", body)


def flags(c):
    text = f"{c.get('title', '')} {c.get('description', '')}"
    out = []
    if re.search(r"\b(post|repost|tweet|retweet|likes?)\b.{0,40}\b(X|Twitter|TikTok|Instagram|Farcaster)\b|\bon X\b", text, re.I):
        out.append("SOCIAL")
    if re.search(r"\bFreebuff\b", text):
        out.append("FREEBUFF")
    if float(c.get("entryFeeUsd") or 0) > 0:
        out.append(f"FEE ${c['entryFeeUsd']}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=6)
    ap.add_argument("--min-reward", type=float, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(hours=args.hours)).isoformat()
    if os.path.exists(STATE):
        with open(STATE, encoding="utf8") as f:
            since = json.load(f).get("last_seen", since)
    data = get("/api/competitions?status=open&limit=200")
    comps = data.get("competitions") or data.get("items") or data
    fresh = [c for c in comps if c.get("publishedAt", "") > since and c.get("deadline", "") > now.isoformat()
             and float(c.get("rewardAmount") or 0) >= args.min_reward]
    fresh.sort(key=lambda c: -float(c.get("rewardAmount") or 0))
    print(f"new bounties since {since[:16]}Z: {len(fresh)}")
    for c in fresh:
        try:
            q = get(f"/api/competitions/{c['slug']}/quota")
            quota = "can submit" if q.get("can_submit") else "NO QUOTA"
        except Exception:
            quota = "quota ?"
        print(f"- ${c.get('rewardAmount')} {c['slug']} | {c.get('title', '')[:60]} | closes {c.get('deadline', '')[:16]}Z | "
              f"{c.get('harnessKind')} | {quota} {' '.join(flags(c))}".rstrip())
    newest = max([c.get("publishedAt", "") for c in comps] + [since])
    if not args.dry_run:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf8") as f:
            json.dump({"last_seen": newest, "checked_at": now.isoformat()}, f)


if __name__ == "__main__":
    main()
