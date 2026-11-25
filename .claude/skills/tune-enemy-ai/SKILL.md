---
name: tune-enemy-ai
description: Build, debug, balance, or test combat enemy AI for playable action games. Use for aggro, target selection, navigation, spacing, attack choices, telegraphs, retreats, boss behavior, behavior-state machines, and deterministic AI regression tests.
---

# Tune Enemy AI

Make enemy choices legible, bounded, and reproducible.

## Model decisions explicitly

Use a small state machine or utility layer with named states such as idle, investigate, pursue, reposition, windup, attack, recover, stagger, retreat, and defeated. State transitions must state their prerequisites, exit conditions, minimum dwell time, and cooldown effects.

## Separate perception, intent, and motion

1. Gather observable inputs: distance, line of sight, target state, occupancy, threat, health, and timers.
2. Select one intention from constrained legal actions.
3. Move and animate toward that intent without rewriting the decision mid-action.

Use authoritative collision and navigation results for movement success. Do not derive them from rendered pose or assumed path completion.

## Preserve fair combat

Telegraph attacks before their active window. Prevent instant turn-and-hit behavior, perpetual chase, clipped attacks through blockers, and repeated recovery spam. Add spacing and commitment so the player can read and answer each enemy archetype.

## Test the decision surface

Create deterministic fixtures for target acquisition, target loss, obstruction, path failure, close-range pressure, multiple enemies, retaliation, interrupt, stagger, boss phase, and reset. Assert transitions and outcomes, not only final positions. Run a real browser encounter after automated tests.

## V3 enrichment — npc-crowd-ai (Ultimate Agent Skills V3, 2026-11-20)

### NPC & crowd (non-combat)

This skill covers *combat* enemy AI (state machines, aggro, telegraphs, bosses). This section adds the *civilian/crowd* side — NPCs that populate a world rather than fight the player:

- **NPC schedules & navigation:** give NPCs schedules (where they are, when, doing what) and navigation that can fail gracefully — a crowd NPC stuck on a corner is a bug, not ambience.
- **Crowd behavior:** model crowd flow (density, avoidance, grouping) separately from individual combat decisions; perception, decision, navigation, and presentation stay separate layers.
- **Staggered updates & bounded simulation tiers:** do not update every NPC every frame — stagger updates and run distant crowds at reduced fidelity (bounded simulation tiers / AI LOD), so crowd size scales without frame-time collapse.
- **Unreachable goals & despawn:** handle goals that cannot be reached (repath, reassign, or despawn safely) — never leave an NPC pathing forever against a wall.

Deliverables: NPC behavior demo, path-failure tests, CPU profile.

Related skills: `build-threejs-enemy-systems` (enemy contracts), `aaa-open-world` (open-world NPC systems), `threejs-performance` (instancing crowds), `threejs-animation` (clip blending for crowds).

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/npc-crowd-ai/SKILL.md
