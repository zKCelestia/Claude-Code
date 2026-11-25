---
name: build-game-inventory
description: Build or repair game inventory, loot, equipment, tooltips, drag-and-drop, persistence, and progression systems. Use for item schemas, pickup flows, stack rules, equipment slots, atomic swaps, save migration, and no-loss regression testing.
---

# Build Game Inventory

Use one typed, serializable item source of truth and make every transfer atomic.

## Define the item contract

Model stable IDs, item definitions, ownership, stack limits, equipment compatibility, effects, rarity, presentation data, and migration version separately. Runtime UI must reference definitions by ID rather than duplicate stats or descriptions.

## Implement transfers as transactions

For pickup, equip, unequip, swap, drag/drop, consume, and sell:

1. Validate source ownership and destination legality.
2. Compute the entire next inventory/equipment state.
3. Commit once or reject without changing either side.
4. Persist only after the committed state is valid.

Never remove an item before confirming a legal destination. Preserve item identity across a swap and prevent duplicate effect registration.

## Build usable UI

Expose slot compatibility, equipped state, quantity, tooltip facts, and failure feedback. Support keyboard and touch alternatives to drag-only interactions. Keep focus behavior, dialogs, and tooltips accessible.

## Test loss boundaries

Cover invalid destinations, full inventory, duplicate pickup, equip swap, mid-action swap, save/load, schema migration, reset/new game, tooltip updates, and repeated dispatch. Validate that total owned item identity is conserved except for explicit consumption or reward rules.

## V3 enrichment — save-persistence (Ultimate Agent Skills V3, 2026-11-20)

### Save & recovery

This skill already covers persistence, save migration, and no-loss regression testing (atomic transfers, one item source of truth). This section consolidates that coverage and adds the failure modes that only appear when saves are attacked by real-world conditions — merged with the existing rules, not duplicated:

- **Version schema & stable IDs:** version the save schema and keep item/entity IDs stable across versions — a migration that renames IDs silently corrupts old saves.
- **Atomic writes / transactions:** write the whole next state or nothing; never leave a half-written save on disk (crash, power loss, and tab-close during save are the test cases).
- **Test corrupt saves, migration, duplication & retry:** deliberately corrupt a save and verify recovery (or clean failure, never silent data loss); test migration from every shipped schema version; test duplicate pickup/reward and retry-after-failure paths so a retried save cannot duplicate items or currency.

Related skills: `threejs-loaders` (caching/disposal) where relevant.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/save-persistence/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`save-systems`**: Save/load engine-neutral: slot, autosave, atomic write, migrasi berversi. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/save-systems/SKILL.md`.
