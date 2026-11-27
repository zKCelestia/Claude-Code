# make.fun tooling

What Liz uses to enter make.fun bounties for @arsyi. The playbook is
`.claude/skills/makefun-workflow/SKILL.md`; the official API/CLI reference is `.claude/skills/makefun/SKILL.md`.

- `news-image/` — the daily news-image front page: `tools/edition.example.mjs` (one day's stories,
  each dated and sourced), `tools/dispatch-page.mjs` (renders `entry.png`, 1024×1024), `tools/art.mjs`
  (original vector drawings), `data/land-110m.json` (Natural Earth land, public domain, from world-atlas),
  `main.ts` (copies the image to `/output`).
- `tools/mock_sheet.py` — puts your judged image beside the entries ranked just above you.
- `tools/submit_source.sh` — bundle, check, submit a source-bundle entry and wait for its score.

Never commit `~/makefun/` (the agent keypair, kits, entry repos) or `~/.makefun/credentials`.
