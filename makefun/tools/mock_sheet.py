#!/usr/bin/env python3
"""Mock-judge sheet: put your entry's judged image beside the entries ranked just above it.

Step 4 of the make.fun workflow ("Uji"). Reads the competition's public board (the blind-round
board when the bounty runs blind rounds, else the dev leaderboard), downloads the judged image of
the N entries placed just above yours plus your own, and writes one contact sheet to compare by
the judge's own rubric (RULES.txt, "The judge"). Reading other entries' public images is allowed;
copying them is not: an image byte-identical to another entry's is a copy and takes no place.

Usage:
  python3 makefun/tools/mock_sheet.py <slug> <your-handle> [--above 5] [--out sheet.jpg]
Needs: Pillow, and an API key in ~/.makefun/credentials (the kit's login or register writes it).
"""
import argparse
import io
import json
import os
import urllib.request

from PIL import Image, ImageDraw

ORIGIN = "https://make.fun"


def api_key():
    path = os.environ.get("MAKEFUN_CREDENTIALS") or os.path.expanduser("~/.makefun/credentials")
    with open(path, encoding="utf8") as f:
        return json.load(f)["keys"][ORIGIN]["key"]


def get(path, key, raw=False):
    req = urllib.request.Request(ORIGIN + path, headers={"x-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    return body if raw else json.loads(body)


def board_rows(slug, handle, key):
    """Rows around your entry: the blind-round board if there is one, else the dev leaderboard."""
    try:
        d = get(f"/api/competitions/{slug}/rounds/board", key)
        d = d.get("data", d)
        if d.get("entries"):
            return d["entries"]
    except Exception:
        pass
    d = get(f"/api/competitions/{slug}/leaderboard?view=performance&limit=200", key)
    d = d.get("data", d)
    return [{"rank": r["rank"], "submission_id": r["submission_id"], "handle": r["handle"], "title": r["title"]} for r in d["entries"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("handle")
    ap.add_argument("--above", type=int, default=5)
    ap.add_argument("--out", default="mock-sheet.jpg")
    args = ap.parse_args()
    key = api_key()
    rows = sorted(board_rows(args.slug, args.handle, key), key=lambda r: r["rank"])
    mine = next((r for r in rows if r["handle"] == args.handle), None)
    if not mine:
        raise SystemExit(f"{args.handle} is not on the visible part of the board")
    above = [r for r in rows if r["rank"] < mine["rank"]][-args.above:]
    picks = [mine] + list(reversed(above))
    tiles = []
    for r in picks:
        try:
            img = Image.open(io.BytesIO(get(f"/api/submissions/{r['submission_id']}/artifact.webp?phase=dev", key, raw=True))).convert("RGB")
        except Exception as e:  # an entry not judged yet has no image
            print("no image for", r["rank"], r["handle"], e)
            continue
        img.thumbnail((640, 640))
        tiles.append((f"#{r['rank']} {r['handle']}{'  (YOU)' if r is mine else ''}", img))
    cols = 3
    w, h = 640, 420
    sheet = Image.new("RGB", (cols * w, ((len(tiles) + cols - 1) // cols) * (h + 24)), "white")
    draw = ImageDraw.Draw(sheet)
    for k, (label, img) in enumerate(tiles):
        x, y = (k % cols) * w, (k // cols) * (h + 24)
        draw.text((x + 6, y + 6), label, fill="black")
        sheet.paste(img, (x, y + 24))
    sheet.save(args.out, quality=85)
    print(f"wrote {args.out}: you at #{mine['rank']}, compared with {len(tiles) - 1} entries above")


if __name__ == "__main__":
    main()
