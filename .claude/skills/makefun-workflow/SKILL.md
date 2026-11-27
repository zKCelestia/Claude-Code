---
name: makefun-workflow
description: The six-step loop Liz uses to enter make.fun bounties for bos (@arsyi) and climb into paid places - scout, research, build from scratch, mock-judge against the live top, verify, submit and learn. Use for any make.fun bounty work in this repo, alongside the official `makefun` skill (the API/CLI reference).
---

# make.fun workflow (Scout · Riset · Build · Uji · Verifikasi · Submit & Belajar)

The official `makefun` skill is the reference for every route and CLI flag. This skill is the
playbook: what to do in order, and what we learned the hard way in the first sessions.

## 0. Before anything: account, keypair, session

- Bos's account is **@arsyi**. Connect, never register: `node cli/makefun.mjs login --keypair ~/makefun/makefun-keypair.json`
  from inside a kit, send bos the `Open … approve code XXXX-XXXX` line, re-run until `Connected`.
- Keep everything in `~/makefun/` (kits, keypair, entry repos), never inside a git repo. Never print the API key.
- **A session can only enter bounties that opened before the session started** (`thinking_in_window`).
  A bounty that opens later needs a new session.
- The transcripts are this session's own Claude Code log (`~/.claude/projects/<cwd>/<id>.jsonl`);
  pass it with `--session`. If the container moved, the newest log is under `~/.claude/projects/-home-user/`.

- Never create a Claude session on bos's behalf for new bounties: its first message shows as if bos
  typed it, and make.fun login and the run record need bos's own typed prompt. Give bos the text to
  paste and let bos open the session.

## 1. Scout

- `GET /api/competitions?status=open` (all pages), keep those with `deadline > now` and `publishedAt <= now`.
- Rank by expected value, not count: bounty size × realistic chance. $2-5 one-liner joke bounties with
  thousands of entries are "watch", not "pursue". Big judged bounties (games $500, news-image $100/day,
  token-radar) are where placing pays.
- Read `/api/competitions/<slug>/requirements` `prerequisites` first; skip what we cannot meet (X account, USDC).

## 2. Riset

- Read the kit's `RULES.txt` sections **The task, The gate, The dossier/judge, Heats, Ranking**.
  The judge's brief is printed word for word: build to its criteria in order.
- Study what wins: finished contests' final top 3 (`/leaderboard?phase=final&limit=3`, then
  `/api/submissions/<id>/artifact.webp?phase=final`), and the live board around you.
- Lessons so far:
  - **Judged images (news-image):** the final judge rewards a page that *reads at a glance* - twelve
    illustrated stories with 3-4 word headlines, big type, a numbers band, a dated map, a date check, a
    sureness legend and sources. Dense small text lost (our 36-story page missed the top 200; the 12-card
    page scored higher in dev).
  - **Judged games:** the judge sees a contact sheet of 3-4 screenshots (cover big) plus a code outline.
    Winners' screenshots are full of live game UI (objective checklists, radio/dialogue, system panels),
    bright saturated colour, motion, and the brief's must-haves dead centre (e.g. a big glowing ring or a
    runway ahead). Use 16:10 (1280×800) so the cover fills the judge's 768×480 box.
  - Dev/provisional rates against house entries are optimistic; only the final heat decides.

## 3. Build (from scratch, in this session)

- **Source bundle, not GitHub** (no About/README branding to set, no repo to create):
  1. `mkdir <repo> && git -C <repo> init`, set git identity to bos's GitHub no-reply
     (`zKCelestia <172098007+zKCelestia@users.noreply.github.com>`), then
     `node <kit>/cli/makefun.mjs init --license MIT --keypair ~/makefun/makefun-keypair.json` **before writing any file**.
  2. Write the entry's code with your own Write/Edit tools in this session. Never clone/copy other
     entries; vendored libraries only as `*.min.js` from npm.
- Reusable pipeline here: `makefun/news-image/` (copy into the anchored repo, write a new
  `tools/edition.mjs` from `edition.example.mjs`, run `node tools/dispatch-page.mjs`, commit `entry.png`).
  News facts: only stories you read yourself dated that day (Wikipedia `Portal:Current_events/<year>_<Month>_<day>`
  plus dated digests); anything from another day goes in the DATE CHECK line. Never invent facts.

## 4. Uji (mock-judge against the live top)

- `python3 makefun/tools/mock_sheet.py <slug> arsyi --above 5 --out sheet.jpg` puts your judged image
  beside the five entries ranked just above you. Look at it and score both against the judge's criteria
  in order; write down where you lose.
- For your own candidate, render it the same way the judge sees it (cover at 768 wide) and compare
  candidate vs your current entry. **Only submit a new version if it clearly wins** - under
  `Force_Last` the newest entry counts even if worse, and blind rounds give no feedback before the final.

## 5. Verifikasi

- Run the program locally (`MAKEFUN_OUTPUT_DIR=out node main.ts`), play/test it headless (Playwright
  is preinstalled), then `makefun/tools/submit_source.sh` runs bundle + `check`; every check must pass.

## 6. Submit & Belajar

- `makefun/tools/submit_source.sh <slug> <repo> "<title>"` submits and waits until the entry is
  `scored`. If anything fails, fix and resubmit before the deadline; if a new version is worse, pick
  the earlier one: `node cli/makefun.mjs final <slug> <submission_id>`.
- After each blind round: `node cli/makefun.mjs rounds <slug>` shows your rank and the five above/below.
- Record outcomes and lessons back into this file.
- **Before the last polish, check you can still submit**: `GET /api/competitions/<slug>/quota`
  (`can_submit`). An account's total per competition can be lowered by "account reputation" with no
  number shown; the daily cap is not the real limit. Spend the last slot on the best version.
- The account may already hold entries from other sessions, and a picked final (`status` says
  "Your final is …"). A picked final counts instead of the newest entry; switching it is bos's call.
- Judge bounties rated against house dashboards: every good entry wins 20/20, so the rate is the
  judge's *margin*. Put each criterion's evidence on the cover itself (radar: watchlist coverage,
  the value formula, held-out tests, an accounting of every protocol, and each row's farm plan with
  effort and cost).

## Results log

- 2026-11-26 `news-image-20261125`: v1 0.969 → v3 0.981 dev; final: outside top 200 (winner 0.816).
- 2026-11-27 `news-image-20261126`: 12-card glanceable page 0.9855 dev (v1 dense 0.980).
- 2026-11-27 `best-flight-game-20261126-0057`: v1 #4003/13,681 (0.508) → v2 #127/17,578 (0.707)
  after radio/objectives/systems/six-pack/16:10 shots; v3 (brighter, ring-ahead cover) in the final.
- 2026-11-27 `token-radar-01`: Dawnwatch (own model tvl+growth+age, CV ×3.54 vs ×5.18 baseline,
  walk-forward, band honesty, 758-protocol accounting, costed farm ledgers) 0.9437 dev, 20/20 won;
  field is dense (#200 at 0.9514). v2 (plan column on every row) built but not submitted: account quota
  for this bounty used up. Bos's earlier entry 01a20882 (0.9428) stays the picked final.
- 2026-11-27 one-liner bounties (blind rounds, results at each deadline): sick-day excuse, Monday
  review, autocorrect fail, production-DB apology, moon comeback. Each a source bundle whose main.ts
  writes /output/entry.txt; drafts revised against the brief's criteria in order before submitting.
- Skipped pump.fun bot sprints ($2 each): the kit's own momentum pilot loses ~95% on the dev tape
  and the guardrails force 20+ round trips into fees; not worth a bot without a real edge.
