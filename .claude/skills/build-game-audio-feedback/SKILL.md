---
name: build-game-audio-feedback
description: Design or implement responsive audio feedback for a Three.js or web game. Use for action sounds, combat layers, music states, spatial audio, mix priorities, mute controls, accessibility, mobile audio unlock, and audio performance.
---

# Build Game Audio Feedback

Use audio to confirm player intent and combat state, not to add constant noise.

## Map feedback

Assign distinct cues for input accepted, windup, contact, block, miss, damage, interrupt, pickup, warning, death, and objective completion. Define priority so critical feedback remains audible during crowded encounters.

## Build for browsers

Unlock audio from a user gesture, respect mute/volume settings, release completed nodes, cap simultaneous voices, and provide subtitles or visual equivalents for meaningful cues. Change music by state with controlled transitions rather than restarts.

## Verify

Test first interaction, rapid actions, pause, tab/background return, mobile, muted state, and reduced motion/accessibility. Check memory and console health after a representative session.

## V3 enrichment — asset-audio (Ultimate Agent Skills V3, 2026-11-20)

### Kreasi audio

This skill covers audio *feedback implementation* (cues, priorities, browser unlock, mix). This section adds the *creation* side — original SFX, ambience, and music:

- **Event cues & loop points:** define which game events get a cue and where loops start/end before recording or composing — a loop that clicks at the seam is a bug, not a style.
- **Original or licensed sounds only:** edit original recordings/compositions, or licensed sounds with the license recorded; never ship audio of unknown provenance.
- **Normalize & encode:** normalize levels across the set and encode to the delivery format; keep the source audio alongside the game export.
- **Test spatial mix & voice budget:** verify the spatial mix in-game and that simultaneous voices stay within budget (this skill's voice cap still applies).

Tooling: Audacity, LMMS, FFmpeg.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/asset-audio/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`audio-design`**: Audio game engine-neutral: bus, slider dB, loudness, ducking, musik adaptif, variasi SFX. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/audio-design/SKILL.md`.
