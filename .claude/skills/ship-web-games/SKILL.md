---
name: ship-web-games
description: Package, deploy, and verify a playable Three.js or web game. Use for release builds, asset delivery, private/public deployment, production smoke tests, browser proof, release notes, rollback readiness, and cleanup of temporary QA resources.
---

# Ship Web Games

Release only a verified commit and prove the deployed game, not merely the local build.

## Release sequence

1. Confirm the exact integration commit and preserve unrelated work.
2. Run focused tests, lint/type checks, production build, and diff checks.
3. Package and deploy the exact validated commit.
4. Poll deployment status and open the production game in the repository-approved browser.

## Production proof

Verify load, first input, one combat or core interaction, assets, save/settings if applicable, responsive view, console health, and representative performance. Report the deployed state separately from local readiness.

## Finish cleanly

Record release evidence and rollback target. Close temporary dev servers, benchmarks, and QA tabs once no longer needed; do not terminate resources owned by another active task.

## V3 enrichment — production-engineering (Ultimate Agent Skills V3, 2026-11-20)

### Engineering & CI

This skill covers the *release* end (verified commit, build, deploy, production smoke test, rollback). This section adds the *upstream engineering foundation* that makes releases repeatable — the work that happens before any release sequence starts:

- **Modular architecture + decision records:** keep the architecture modular, record decisions and public contracts, choose dependencies with approved licenses and predictable maintenance.
- **Git + pinned tools/dependencies:** maintain the repo, ignore generated caches, track permitted large source assets appropriately, pin tools and dependencies, support repeatable local builds. Never commit API keys, private data, or vendor content without permission.
- **Build/test/lint from a clean checkout:** define the commands so a fresh checkout builds, tests, and lints; add lightweight local CI scripts first (self-hosted CI is optional).
- **Separate dev/staging/prod:** separate local development, staging, and production data/config — a release must never read dev data by accident.
- **Migrations, backups, rollback & logs:** use incremental changes, migrations, backups, rollback, scoped permissions, and structured logs. For backend games, prioritize server authority, durable transactions, rate limits, and resource budgets.
- **Supply chain & cost:** review supply-chain changes, identify offline/free alternatives; do not silently add subscriptions, hosted services, or cloud billing. Note infrastructure costs when publishing multiplayer services.

Deliverables: release manifest, versioned artifacts, attribution/credits, known issues, test evidence, runbook.

Related skills: `test-playable-web-games` (the QA side of the same release).

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/production-engineering/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`itch-publish`**: Publikasikan/update game di itch.io via butler CLI: `butler push`, channel platform, build HTML5, `--userversion`, CI upload. Temuan review: Catatan kredensial defensif (lihat atas): `BUTLER_API_KEY` via secret CI, login via browser user; peringatan revoke bila key tercetak di log. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/workflows/itch-publish/SKILL.md`.
- **`steam-publish`**: Publikasikan/update game di Steam via Steamworks + SteamPipe: depot, script app_build .vdf, upload steamcmd, beta branch, SetLive, review store. Temuan review: Catatan kredensial defensif (lihat atas): password akun Steam + token login `config.vdf` — jangan pernah di-commit; password dilarang di argumen CLI. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/workflows/steam-publish/SKILL.md`.
