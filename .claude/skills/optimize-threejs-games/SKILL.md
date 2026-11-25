---
name: optimize-threejs-games
description: Profile, diagnose, and improve Three.js or WebGL game performance without regressing gameplay. Use for frame-time drops, CPU/GPU pressure, draw calls, texture and geometry budgets, animation loops, adaptive quality, mobile performance, and browser performance verification.
---

# Optimize Three.js Games

Measure before changing behavior, then validate the same gameplay path after every optimization.

## Establish a repeatable scene

Choose a deterministic representative encounter and record device, viewport, quality level, player position, enemies, active effects, frame-time sample, draw calls, triangles, texture count, and warnings. Compare like with like.

## Diagnose the limiting side

- Suspect CPU when simulation, allocations, React work, pathfinding, or per-frame scans grow with actors.
- Suspect GPU when resolution, overdraw, shadows, transparent particles, post-processing, draw calls, geometry, or texture bandwidth dominate.
- Inspect before optimizing; do not lower quality blindly.

## Apply low-risk fixes first

Reuse geometry/materials, pool transient effects, cull inactive/offscreen work, throttle noncritical UI updates, cap particle counts, avoid per-frame allocation, and update only changed transforms. Keep render quality settings explicit and reversible. Degrade decorative effects before combat readability or controls.

## Guard the result

Re-run the original encounter and verify frame time, visual correctness, collision/contact behavior, memory stability, mobile controls, reduced motion, and console health. Close temporary servers, benchmarks, and browser tabs once they are no longer needed.

## V3 enrichment — rendering-performance (Ultimate Agent Skills V3, 2026-11-20)

### Disiplin pengukuran

This skill already measures, diagnoses, and fixes performance on a repeatable scene. This section adds the explicit *measurement discipline* that governs every optimization pass — so a "fix" is proven, not asserted:

- **Baseline first:** measure the baseline (frame time, draw calls, triangles, texture count, memory) on the representative scene before changing anything.
- **Target device + budget:** name the target device and the budget (frame-time target, draw-call ceiling) up front — an optimization without a budget has no done condition.
- **Identify the bottleneck (CPU vs GPU):** CPU when simulation, allocations, pathfinding, or per-frame scans grow with actors; GPU when resolution, overdraw, shadows, transparent particles, post-processing, draw calls, or texture bandwidth dominate. Inspect before optimizing; do not lower quality blindly.
- **Change one variable at a time:** a single change per measurement, then re-measure the same gameplay path — two simultaneous changes make the result unreadable.

Deliverables: before/after metrics, profiler capture (RenderDoc, Tracy, meshoptimizer), visual comparison.

Related skills: `threejs-performance` (the deep reference for what to measure), `threejs-lighting` (shadow cost), `threejs-shaders` (shader stalls), `threejs-postprocessing` (cost per pass).

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/rendering-performance/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`performance-optimization`**: Diagnosis frame-rate lewat pengukuran: CPU vs GPU, draw call, pooling, GC spike (Godot/Unity/Unreal/Roblox). File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/performance-optimization/SKILL.md`.
