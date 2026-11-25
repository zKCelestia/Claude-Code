---
name: create-game-vfx
description: Create readable, performance-safe Three.js game visual effects. Use for attacks, impacts, damage feedback, status effects, spell trails, particles, shaders, telegraphs, quality tiers, and reduced-motion alternatives.
---

# Create Game VFX

Make the gameplay meaning visible before adding spectacle.

## Specify

For every effect define trigger, owner, duration, gameplay meaning, camera-distance silhouette, color hierarchy, spawn cap, cleanup rule, and reduced-motion equivalent. Separate telegraph, contact, success, failure, and lingering status visuals.

## Implement safely

Pool short-lived objects, reuse materials/geometry, cap particles, and avoid per-frame allocation. Use additive/transparency sparingly around important UI and targets. Make cleanup idempotent so reset, death, and pause cannot leak effects.

## Verify

Test overlaps, multiple targets, rapid repetition, pause/resume, lowest quality, reduced motion, and touch viewports. Sample the live encounter for warnings, draw calls, frame time, and visual readability.

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`game-feel`**: Juice: trauma shake, hit-stop, easing, squash & stretch, knockback. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/game-feel/SKILL.md`.
- **`shader-programming`**: Teknik shader engine-neutral GLSL + ekuivalen HLSL: dissolve, outline, fresnel, post effect. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/shader-programming/SKILL.md`.
- **`unreal-niagara`**: VFX Niagara UE 5.8: system, emitter, parameter User, spawn dari C++/Blueprint, bound, sim GPU vs CPU. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/unreal/unreal-niagara/SKILL.md`.
