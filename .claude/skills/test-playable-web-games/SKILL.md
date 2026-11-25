---
name: test-playable-web-games
description: Test a playable browser game end to end with deterministic fixtures and real browser evidence. Use for gameplay QA, regression testing, controls, accessibility, responsive/mobile testing, save flows, console checks, performance smoke tests, and release verification.
---

# Test Playable Web Games

Combine deterministic tests with short real playthroughs. Do not treat a green build as gameplay proof.

## Start with a test matrix

Map the player journey: launch, new game, controls, core action, enemy encounter, reward, inventory/progression, save/continue, loss/retry, pause, settings, and completion. Add device variants for desktop keyboard/mouse, touch portrait, touch landscape, and reduced motion.

## Prefer deterministic review states

Create seedable fixtures, debug routes, or query parameters for combat phase, inventory loadout, boss phase, tutorial step, save migration, low health, and error states. Test important transitions directly rather than grinding through the campaign.

## Verify the player experience

Use the repository-approved browser surface and honor local browser restrictions. Confirm screen-visible feedback after each meaningful action: control response, target state, damage/resource state, UI update, and navigation. Inspect console warnings/errors and sample performance only on a representative live scene.

## Report actionable evidence

Record reproduction steps, expected versus actual result, severity, device/viewport, and the shortest useful proof. Separate new regressions from pre-existing baseline issues. After testing, close idle browser pages, dev servers, and benchmarks while leaving active task resources alone.

## V3 enrichment — production-qa (Ultimate Agent Skills V3, 2026-11-20)

### QA rilis & profiling

This skill covers end-to-end gameplay QA (test matrix, deterministic fixtures, playthroughs, save flows, console, performance smoke tests). This section adds the *release-readiness* layer on top of it:

- **Acceptance criteria → test matrix:** convert requirements into observable acceptance criteria and a test matrix covering platform, input type, lifecycle, normal use, edge conditions, and failures.
- **Deterministic tests + clean build + engine smoke test:** run deterministic core tests, a clean build, and an engine smoke test — a green local build is not release proof.
- **Profiling on target hardware:** profile representative scenes/builds and record version, device, scene, settings, p50/p95 frame time, memory, and measured bottlenecks. No fabricated metrics and no unmeasured optimization claims.
- **License, migration & multiplayer checks:** check asset licenses, import settings, accessibility, localization, save migration, and error handling; for multiplayer/persistence add invalid-intent, reconnect, retry, duplication, and safe-recovery checks.
- **Classify issues by impact:** reproduce before fixing, add a regression test, rerun the relevant checks. Mark a test PASS only with executed evidence — otherwise FAIL, NOT RUN, or BLOCKED. Do not publish without explicit approval.

Related skills: `threejs-performance` (profiling reference).

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/production-qa/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`prototype-fast`**: Bangun prototype throwaway ~1 jam untuk jawab satu pertanyaan ("apakah mekanik ini fun?"): brief, greybox, debug HUD, playtest, keputusan keep/kill/retune. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/workflows/prototype-fast/SKILL.md`.
