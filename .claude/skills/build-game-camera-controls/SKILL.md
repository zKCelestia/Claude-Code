---
name: build-game-camera-controls
description: Implement or tune Three.js game cameras. Use for isometric framing, follow behavior, orbit/zoom limits, occlusion, lock-on, camera shake, touch camera controls, and camera regression tests.
---

# Build Game Camera Controls

Keep gameplay readable before making the camera cinematic. Define one authoritative target, camera bounds, zoom range, collision/occlusion policy, and reduced-motion behavior.

## Implement

- Smooth position and look-at targets independently; never bind the camera directly to jittery render state.
- Preserve player, immediate threat, objective, and interaction cues in frame at the intended distance.
- Clamp orbit, pitch, and zoom; prevent walls or props from hiding the player without making geometry invisible globally.
- Treat lock-on, scripted moments, and shake as temporary modifiers layered over the base camera.
- On touch, separate camera gesture zones from movement/action controls and provide reset framing.

## Verify

Test corners, tall props, tunnels, multiple enemies, lock-on switching, pause, reduced motion, portrait, and landscape. Confirm no camera behavior breaks targeting, UI, or performance.

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`camera-systems`**: Kamera 2D follow/deadzone/look-ahead, orbit 3D, first-person, split-screen (Godot + Cinemachine 3). File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/camera-systems/SKILL.md`.
- **`input-systems`**: Arsitektur input engine-neutral: named action, deadzone, buffer, rebinding (kode Godot InputMap). File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/input-systems/SKILL.md`.
