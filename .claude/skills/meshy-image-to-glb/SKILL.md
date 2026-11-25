---
name: meshy-image-to-glb
description: >-
  Convert 2D images / concept-art PNGs into optimized GLB 3D models using Meshy AI
  (image-to-3D → remesh → optional auto-rig with walk/run → optional compression),
  then save them into the game's public/models folder. Use when adding or replacing
  3D characters, NPCs, or props in the Delivery Runner game from flat images, or any
  time someone asks to "turn this image into a 3D model / GLB" via Meshy.
---

# Meshy: image → GLB (for the game)

Turn a flat image into a game-ready `.glb` and drop it into the right `public/models/` slot.
The bundled [`scripts/meshy.sh`](scripts/meshy.sh) runs the whole Meshy pipeline end-to-end; this
file tells you which mode to use, where to save, and how the game consumes the result.

## When to use
- Adding/replacing a **character** (rigged, animated) — e.g. the player or the pursuer.
- Adding/replacing a **prop** or **NPC** (static, no skeleton) — crates, packages, scooters, sellers.
- Anyone says "convert this PNG to 3D / GLB", "make a 3D model from this art", or "use Meshy".

## Prerequisites
- **Meshy API key** in the `MESHY_KEY` env var (or pass `--key`). Get it from the Meshy dashboard.
  **Never commit the key.** Treat any key pasted in chat as compromised — rotate it after use.
- Tools: `curl`, `python3` (always). `--compress` also needs `npx` (it fetches `@gltf-transform/cli`).
- Run from anywhere; pass an absolute `--out` path into the game.

```bash
export MESHY_KEY="msy_xxx"   # set once per shell; do not hardcode in files
```

## Quick start

The game's models live under `delivery-runner/game/public/models/`. Pick the mode by asset type:

```bash
SKILL=/Users/dribrahimm/1-Games/.agents/skills/meshy-image-to-glb
GAME=/Users/dribrahimm/1-Games/delivery-runner/game/public/models

# 1) CHARACTER — rigged + walk/run animation, compressed (player / pursuer)
"$SKILL/scripts/meshy.sh" --mode rigged  --height 1.8 --compress \
  --image ~/art/player.png --out "$GAME/player.glb"

# 2) NPC — static seller/customer, low-poly, compressed
"$SKILL/scripts/meshy.sh" --mode static --polycount 9000 --compress \
  --image ~/art/fruit_seller.png --out "$GAME/npcs/fruit_seller.glb"

# 3) PROP — static crate/package/scooter, low-poly, compressed
"$SKILL/scripts/meshy.sh" --mode static --polycount 10000 --compress \
  --image ~/art/scooter.png --out "$GAME/props/scooter.glb"
```

Each run prints live progress (`image-to-3d → remesh → [rigging] → download → compress`) and the final
byte size. Runs take a few minutes (Meshy generation + polling).

## The pipeline (what the script does)
1. **image-to-3D** — uploads the image as a base64 data URI, generates a textured mesh.
2. **remesh** — reduces polycount (default rigged 20k / static 10k). **Required** before rigging
   (raw meshes are ~500k faces; the rig limit is 300k) and good for everything (mobile budget).
3. **rigging** *(rigged mode only)* — adds a skeleton + **walk/run** clips at `--height` metres,
   then picks the animated GLB.
4. **download** the GLB to `--out`.
5. **compress** *(with `--compress`)* — `gltf-transform optimize` with `quantize` + WebP textures,
   ~10–30× smaller. Uses **KHR_mesh_quantization + EXT_texture_webp**, which three.js loads with
   **no extra decoder** (unlike Draco/meshopt).

## Where to save (Delivery Runner)
| Asset | Mode | Path under `game/public/models/` | Notes |
| --- | --- | --- | --- |
| Player | rigged | `player.glb` | needs run animation |
| Pursuer/guard | rigged | `pursuer.glb` | needs run animation |
| Sellers/customers | static | `npcs/<name>.glb` | e.g. `fruit_seller`, `baker`, `tea_seller`, `shopper_bags`, `elderly`, `boy` |
| Crate / package / scooter | static | `props/<name>.glb` | `crate`, `package`, `scooter` |

## How the game consumes it
- **Do not pre-scale/orient in the model** — the game's loader normalizes on load: it scales each model
  to a target height, centers it, drops feet to the ground, and rotates 180° to face into the screen.
  So `--height` only matters for the rig; final on-screen size is set in code.
- Characters load via the player/pursuer loader; NPCs/props are cloned from the GLB into the existing
  pools (sellers along the sides, package/scooter pickups). Replacing a file at the same path is enough —
  no code change needed if you keep the filename.
- Loader has a **HEAD-probe + procedural fallback**, so a missing/failed model never hard-crashes the game.

## Gotchas (full list in [reference.md](reference.md))
- Rigging fails over **300k faces** → always remesh first (the script does).
- The remesh route is **`/openapi/v1/remesh`** even though an error once said `v2`.
- Auto-rig only yields **walk + run** (no jump/roll) — fine for this game; use Mixamo later for more.
- Script is **bash-3.2 safe** (macOS) — no associative arrays.

## Files
- [`scripts/meshy.sh`](scripts/meshy.sh) — the end-to-end converter (run with `--help`).
- [`reference.md`](reference.md) — API endpoints, parameter tables, polycount/height guidance, troubleshooting.

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`create-game-assets`**: Rencanakan/generate/source/validasi aset art konsisten + manifest + provenance/lisensi + QA raster. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/create-game-assets/SKILL.md`.
