---
name: design-game-encounters
description: Design, implement, tune, or test Three.js action-game encounters. Use for arena layout, enemy composition, spawn pacing, objectives, boss phases, reward cadence, encounter fixtures, and difficulty validation.
---

# Design Game Encounters

Design encounters as decisions, not actor counts.

## Compose

Define objective, available space, enemy roles, spawn timing, hazards, player resources, exits, failure recovery, and reward. Add one pressure source at a time; require each archetype to create a distinct response.

## Keep it fair

Protect readable paths, telegraphs, camera sight lines, and recovery windows. Cap simultaneous committed attackers and avoid offscreen damage, unavoidable chains, or encounter resets that duplicate rewards.

## Validate

Create deterministic starts for low resources, each wave, boss phase, victory, and death/retry. Test desktop and mobile at the real camera distance, then adjust composition from observed decisions rather than raw completion time.

## V3 enrichment — mission-dialogue (Ultimate Agent Skills V3, 2026-11-20)

### Misi & dialog

This skill composes encounters (arena, spawn, boss phase, reward). This section adds the *mission and dialogue layer* that sits on top of encounters — quest state, branching, and continuity across sessions:

- **Mission graph:** model quests as a graph with state and prerequisites — which missions unlock what, and what must be true before a mission starts.
- **Branching dialogue:** author dialogue branches with explicit conditions; every branch must be reachable by some play path, or it is cut.
- **Idempotent rewards:** a reward must be safe to grant twice (replay, retry, save reload) without duplicating items, currency, or flags.
- **Validate unreachable branches:** test the graph for branches no player can reach and quests that can soft-lock (prerequisite never satisfiable).
- **Localization & persistence integration:** dialogue and quest state must survive save/load and work with localized text — quest IDs and dialogue keys are stable, never display strings.

Tooling: ink, YarnSpinner.

Deliverables: mission graph, dialogue tests, replay/save continuity proof.

Related skills: `game-idea-to-gdd` (quest structure in the GDD), `build-threejs-enemy-systems` (enemy contracts the encounters use), `tune-enemy-ai`.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/mission-dialogue/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`ai-behavior-trees-utility-ai`**: BT + utility AI engine-neutral (C#, Blackboard, response curve). File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/ai-behavior-trees-utility-ai/SKILL.md`.
- **`game-ai`**: AI musuh/NPC engine-neutral: pilih FSM/BT/utility/GOAP, persepsi, steering, A*. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/game-ai/SKILL.md`.
