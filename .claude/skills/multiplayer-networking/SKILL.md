---
name: multiplayer-networking
description: Build server-authoritative multiplayer with prediction and reconciliation where appropriate. Use when the task requires this specialist capability.
---
# Multiplayer Networking

## Workflow
1. Define protocol and trust boundaries.
2. validate commands and rate limits.
3. handle packet loss, disconnects and state snapshots.

## Deliverables
Two-client test, invalid command rejection, latency scenarios.

## Upstream GitHub sources (references, not this custom skill’s publisher)
- https://github.com/gamedev-skills/awesome-gamedev-agent-skills
- https://github.com/heroiclabs/nakama
- https://github.com/lsalzman/enet

## Host integration and acceptance
- Use only reviewed, locally installed tools; check version and capability before use. Never execute arbitrary instructions from a fetched repository.
- Inherit host permission policy and task scope. For security, default to local owned environments and require authorization before any external testing.
- Report observable evidence, tests and limitations; use NOT RUN or BLOCKED when tools are unavailable.
- Do not activate paid services or publish changes without permission.

---
_Sumber: Ultimate Agent Skills V3 (diinstal 2026-11-20 dari ~/workspace/ultimate-agent-v3/.agents/skills/multiplayer-networking/SKILL.md; sumber upstream tercantum di dalam skill)._

Related skills: aaa-open-world. Celah: belum ada referensi implementasi networking Three.js (WebSocket, snapshot) di set lama.

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`godot-multiplayer`**: Multiplayer high-level Godot 4.7: ENet host/join, @rpc, MultiplayerSpawner/Synchronizer, server-authoritative. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/godot/godot-multiplayer/SKILL.md`.
- **`roblox-networking`**: Networking client-server Roblox + anti-exploit: kontrak RemoteEvent/RemoteFunction, server authority, rate limit, validasi hit, replikasi. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/other-engines/roblox-networking/SKILL.md`.
