#!/usr/bin/env python3
"""Mock judge: pit two make.fun entries against each other with the bounty's real judge model.

Step 4 of the make.fun workflow ("Uji"). Reads the judge's sealed instructions word for word from
the kit's RULES.txt, shows the model Entry A and Entry B the way make.fun's judge view does (one
contact sheet per entry: the cover fitted in 768x480, the other screenshots in a row beneath it, plus
an optional short outline text), and plays one game: two calls, one in each order. Each call gives
the entry it picks 0.5 + margin/10, as make.fun scores it. Text entries (one-liners) go in as text.

Usage:
  python3 makefun/tools/judge_ab.py --rules <kit>/RULES.txt \
      --a <screenshots dir | image ...> --b <screenshots dir | image ... | submission:<id>> \
      [--a-outline file] [--b-outline file] [--games 1] [--model z-ai/glm-5.3-flash]
  python3 makefun/tools/judge_ab.py --rules <kit>/RULES.txt --a-text "line A" --b-text "line B"

Needs: Pillow; network to openrouter.ai, whose key the session's proxy injects (no key in code);
for submission:<id>, the make.fun API key in ~/.makefun/credentials.
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.request

from PIL import Image

OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
ORIGIN = "https://make.fun"
FORMAT = (
    "Compare the two against those criteria, pick the one that meets them better with no tie, and "
    "answer with a short reason, a verdict naming A or B, and a margin from 1 (by a hair) to 5 "
    "(overwhelmingly better). Answer only with JSON: "
    '{"reason": "<short reason>", "verdict": "A" or "B", "margin": 1-5}'
)


def judge_prompt(rules_text):
    """The judge's sealed instructions, as RULES.txt quotes them word for word."""
    start = re.search(r"(word for word:|published here in full:)\s*\n", rules_text)
    end = rules_text.find("After them the house adds", start.end() if start else 0)
    if not start or end < 0:
        raise SystemExit("could not find the judge's instructions in RULES.txt")
    return rules_text[start.end():end].strip()


def mf_get(path):
    with open(os.path.expanduser("~/.makefun/credentials"), encoding="utf8") as f:
        key = json.load(f)["keys"][ORIGIN]["key"]
    req = urllib.request.Request(ORIGIN + path, headers={"x-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def load_images(spec):
    """A screenshots directory (sorted by name, the first is the cover), image files, or
    submission:<id> (that entry's judged images from make.fun)."""
    if len(spec) == 1 and spec[0].startswith("submission:"):
        sid = spec[0].split(":", 1)[1]
        images = []
        for i in range(4):
            q = f"&image={i}" if i else ""
            try:
                images.append(Image.open(io.BytesIO(mf_get(f"/api/submissions/{sid}/artifact.webp?phase=dev{q}"))).convert("RGB"))
            except Exception:
                break
        if not images:
            raise SystemExit(f"no judged image for submission {sid}")
        return images
    files = []
    for s in spec:
        if os.path.isdir(s):
            files += sorted(os.path.join(s, f) for f in os.listdir(s) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and not f.startswith("."))
        else:
            files.append(s)
    return [Image.open(f).convert("RGB") for f in files]


def contact_sheet(images):
    """The cover fitted in 768x480 on top, the others in a row of smaller cells beneath it."""
    cover = images[0].copy()
    cover.thumbnail((768, 480))
    rest = images[1:]
    cell_w = 768 // max(1, len(rest))
    cells = []
    for im in rest:
        c = im.copy()
        c.thumbnail((cell_w - 4, 240))
        cells.append(c)
    height = cover.height + (max(c.height for c in cells) + 6 if cells else 0)
    sheet = Image.new("RGB", (768, height), "white")
    sheet.paste(cover, ((768 - cover.width) // 2, 0))
    for i, c in enumerate(cells):
        sheet.paste(c, (i * cell_w + 2, cover.height + 6))
    out = io.BytesIO()
    sheet.save(out, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode()


def entry_parts(label, sheet, outline, text):
    parts = [{"type": "text", "text": f"Entry {label}:"}]
    if text is not None:
        parts.append({"type": "text", "text": text})
    if sheet:
        parts.append({"type": "image_url", "image_url": {"url": sheet}})
    if outline:
        parts.append({"type": "text", "text": f"Entry {label} source outline:\n{outline}"})
    return parts


def call(model, system, first, second, effort):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": first + second + [{"type": "text", "text": FORMAT}]},
        ],
        "max_tokens": 6000,
        "reasoning": {"effort": effort},
    }
    req = urllib.request.Request(OPENROUTER, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json",
        # The session's proxy replaces this placeholder with the saved OpenRouter key.
        "Authorization": "Bearer proxy-injected",
    })
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    content = data["choices"][0]["message"].get("content") or ""
    m = re.search(r"\{.*\}", content, re.S)
    if not m:
        return None, content
    try:
        v = json.loads(m.group(0))
        return {"verdict": str(v["verdict"]).strip().upper()[:1], "margin": max(1, min(5, int(v["margin"]))), "reason": v.get("reason", "")}, content
    except Exception:
        return None, content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--a", nargs="+")
    ap.add_argument("--b", nargs="+")
    ap.add_argument("--a-text")
    ap.add_argument("--b-text")
    ap.add_argument("--a-outline")
    ap.add_argument("--b-outline")
    ap.add_argument("--games", type=int, default=1)
    ap.add_argument("--model", default="z-ai/glm-5.3-flash")
    ap.add_argument("--effort", default="high")
    args = ap.parse_args()

    with open(args.rules, encoding="utf8") as f:
        system = judge_prompt(f.read())
    read = lambda p: open(p, encoding="utf8").read()[:6000] if p else None
    sides = {}
    for label, imgs, text, outline in (("A", args.a, args.a_text, args.a_outline), ("B", args.b, args.b_text, args.b_outline)):
        sides[label] = (contact_sheet(load_images(imgs)) if imgs else None, read(outline), text)

    score = {"A": 0.0, "B": 0.0}
    calls = 0
    for g in range(args.games):
        for order in (("A", "B"), ("B", "A")):
            # The model always sees the first entry as "Entry A"; map its verdict back.
            first = entry_parts("A", *sides[order[0]])
            second = entry_parts("B", *sides[order[1]])
            v, raw = call(args.model, system, first, second, args.effort)
            calls += 1
            if not v:
                score["A"] += 0.5
                score["B"] += 0.5
                print(f"game {g + 1}, {order[0]} shown first: no verdict ({raw[:120]!r})")
                continue
            picked = order[0] if v["verdict"] == "A" else order[1]
            other = "B" if picked == "A" else "A"
            share = 0.5 + v["margin"] / 10
            score[picked] += share
            score[other] += 1 - share
            print(f"game {g + 1}, {order[0]} shown first: picks {picked} by {v['margin']} - {v['reason'][:300]}")
    print(f"\nscore over {calls} calls: A {score['A'] / calls:.3f}  B {score['B'] / calls:.3f}  ->  "
          f"{'A' if score['A'] > score['B'] else 'B' if score['B'] > score['A'] else 'level'} wins")


if __name__ == "__main__":
    sys.exit(main())
