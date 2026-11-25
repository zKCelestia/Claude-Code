---
name: blender-game-3d
description: >-
  Create, convert, and optimize 3D models for game development across web
  (Three.js GLB), iOS (RealityKit USDZ), and Android (Filament glTF) using
  Blender — driven by the Blender MCP server when connected, or the headless
  Blender CLI (blender --background --python) otherwise. Use when someone asks
  to make/convert/optimize a 3D asset or character, export a GLB/USDZ/glTF,
  get a model "ready for iOS/Android/web", fix a model that won't load or
  animate in RealityKit/Three.js/Filament, or "use the Blender MCP".
---

# Blender → game 3D assets (web · iOS · Android)

Model **once** in Blender, export **per platform** with the right format, textures, and
skeleton/animation rules. This skill encodes the platform matrix + the gotchas that actually
bite (proven on the Run Over project: Meshy GLB → web GLB / iOS USDZ).

Deep web/Three.js reference: [`/Users/dribrahimm/1-Games/blender-3d.md`](../../blender-3d.md) — read it
for baking, KTX2, Draco/Meshopt, color-space, the full export-preset table. This skill is the
**multi-platform action layer** on top of it.

## When to use
- "Make a 3D model / character / prop for the game" → author in Blender, export per target.
- "Get this GLB ready for iOS / Android / web" → convert + optimize to the target format.
- "The character won't load / won't animate in RealityKit (or Three.js / Filament)" → fix + re-export.
- Upstream: a flat image → use the **meshy-image-to-glb** skill first to get a GLB, then this skill to target each platform.

## Two ways to drive Blender
1. **Blender MCP (preferred when connected)** — the official server at
   <https://www.blender.org/lab/mcp-server/> (v1.0.0 for Blender ≥ 5.1). It exposes tools to run
   Python *inside a live Blender*, inspect the scene, and iterate visually. **Check first** whether
   Blender MCP tools are registered in your session (search tools for "blender"); if none appear,
   it isn't connected — use the CLI. To connect it: install the add-on in Blender, then add the
   server to the agent's MCP config and reconnect. (In headless/CI contexts it usually won't be — that's fine.)
2. **Headless Blender CLI (always works, reproducible)** — what this skill's scripts use:
   ```sh
   /Applications/Blender.app/Contents/MacOS/Blender --background --python <script.py> -- <args>
   ```
   No MCP needed; ideal for batch convert/export and CI. Blender 5.1+ verified.

Same Python (`bpy`) either way — the MCP just runs it live. Prefer the CLI for deterministic
batch jobs; use the MCP when you need to *see* the result and iterate.

## Platform export matrix (the core)
| Target | Format | Textures | Geometry compression | Skeleton/anim notes |
| --- | --- | --- | --- | --- |
| **Web (Three.js)** | **`.glb`** | WebP (`EXT_texture_webp`) **or** KTX2 | **Meshopt+quantize** (decoder-free-ish) or **Draco** | +Y Up on; **4 bone weights**; Custom Props → `extras` |
| **iOS (RealityKit)** | **`.usdz`** | **PNG/JPEG only — never WebP** | none (USD has no Draco/Meshopt) | **defined single skeleton root**; avoid baked node scale; UsdSkel anim |
| **Android (Filament)** | **`.glb`/`.gltf`** | KTX2 (best) or PNG | Draco **or** Meshopt (gltfio supports both) | same as web; 4 weights |

**Golden rule:** keep textures **PNG/JPEG in the Blender source**. WebP and mesh-quantization are
**post-export web optimizations** (apply with `gltf-transform`), and they actively *break* the USDZ
path — so derive iOS USDZ from an **un-WebP, un-quantized** GLB/scene.

## Recipes

### A. GLB → iOS USDZ (the fragile one — use the script)
RealityKit can't load GLB and its GLTFKit2 path mis-handles skinned animation; **USDZ is the
reliable skeletal path**. Blender re-authors a clean skeleton on import (fixing glTF `skeleton:null`)
and exports UsdSkel.
```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/glb_to_usdz.py -- --input player.glb --output player.usdz
```
The script: imports → **drops stray meshes** (Meshy leaves an `Icosphere`) → **forces textures to
PNG** (kills WebP) → exports USDZ with animation → **re-imports to verify** the skeleton + clip
survived. If the input GLB is WebP/quantized, transcode it first:
```sh
npx @gltf-transform/cli@4 dequantize in.glb tmp.glb
npx @gltf-transform/cli@4 png       tmp.glb clean.glb --formats webp   # WebP→PNG
```
Then on the iOS side **normalize on load** (scale-to-height, feet-to-ground, wrapper node) — Meshy
rigs import at ~1 cm with scale baked in; don't fight it in Blender, normalize in the engine.

### B. Author/fix in Blender → web GLB
Export with the locked preset (`scripts/export_gltf.py`, or in the MCP via `bpy.ops.export_scene.gltf`):
`+Y Up` on · `Tangents` on if normal-mapped · `Skinning` limited to **4** · `Custom Properties` on
(→ `extras` → `userData`) · `Apply Modifiers` per-asset · Animations = **Actions** + sample.
Then optimize as a **build step** (not in Blender):
```sh
# decoder-free web (Three.js loads with no Draco/KTX2 decoder): quantize + WebP
npx @gltf-transform/cli@4 optimize in.glb web.glb --compress quantize --texture-compress webp --texture-size 1024
# or max-compression: Draco + KTX2 (needs DRACOLoader + KTX2Loader wired in Three.js)
npx @gltf-transform/cli@4 optimize in.glb web.glb --compress draco   --texture-compress ktx2
```

### C. web GLB → Android (Filament) GLB
Filament/`gltfio` loads standard glTF and supports Draco/Meshopt + KTX2. Reuse the web GLB; prefer
**KTX2** textures (transcodes to ASTC on Android) and Meshopt:
```sh
npx @gltf-transform/cli@4 optimize in.glb android.glb --compress meshopt --texture-compress ktx2 --texture-size 1024
```

## Pitfalls that actually bite (condensed; full list in blender-3d.md §"Top pitfalls")
- **USDZ + WebP / quantization → broken or untextured.** Always feed USDZ a PNG, un-quantized source.
- **RealityKit won't animate the GLB** → go through Blender → USDZ (defined skeleton, UsdSkel).
- **Stray geometry** (Meshy `Icosphere`, helper objects) ships into the export — strip non-character meshes.
- **>4 bone weights** → Three.js/RealityKit drop the extras (jitter, splayed fingers). Limit to 4 in Blender.
- **Unapplied transforms / odd scale** → arrives scaled/rotated. Apply All Transforms; or normalize on load.
- **Procedural shader nodes / Geometry Nodes / particles don't export** → bake to image textures / realize first.
- **Color-space**: albedo+emissive = sRGB; normal/roughness/metallic/AO = Non-Color.
- **`bpy` operator args differ by Blender version** — e.g. USD `export_textures` is unsupported in 5.1. The scripts try a rich arg set then fall back to a minimal one.
- **Verify before shipping**: re-import the USDZ (the script does) / open the GLB in
  `gltf-transform inspect` + Don McCurdy's glTF viewer.

## Files
- [`scripts/glb_to_usdz.py`](scripts/glb_to_usdz.py) — headless GLB→USDZ for iOS (strip strays, PNG, preserve anim, verify).
- [`scripts/export_gltf.py`](scripts/export_gltf.py) — headless `.blend`/scene → web/Android GLB with the locked game preset.
- [`reference.md`](reference.md) — per-platform deep notes, MCP setup, gltf-transform recipe library, normalize-on-load snippets.
- Deep web reference: [`../../blender-3d.md`](../../blender-3d.md).

## V3 enrichment — asset-3d-procedural (Ultimate Agent Skills V3, 2026-11-20)

### Prosedural di Blender

Procedural authoring inside the canonical Blender flow (model once in Blender, export per platform — see the platform matrix above). Applies to modular props, terrain, buildings, and vehicles:

- **Consistent units, topology, UVs, pivots, collision, and LOD** for every procedural asset — a procedural prop must meet the same contract as an authored one (same unit scale, clean topology, correct pivot, usable collision, LOD where it matters).
- **Export to the engine format** (GLB for web, USDZ for iOS, glTF for Android — per the matrix above), then **inspect the imported model** in the target engine: transform, materials, normals, and collision must survive the round-trip.
- **Modular by design:** build from reusable modules with stable sockets/pivots so variants compose without re-authoring.

Related skills: `img2threejs` (if the source is a reference image and the target is Three.js code, use that skill instead of Blender), `threejs-geometry` (procedural geometry in code), `threejs-loaders` (GLB/Draco loading), `build-hybrid-game-assets` (which representation to pick before entering Blender).

Brief, budget & provenance for these assets: lihat seksi "Brief, budget & provenance" di `build-hybrid-game-assets` (V3 enrichment — game-asset-pipeline) — tidak diduplikasi di sini.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/asset-3d-procedural/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`create-game-assets`**: Rencanakan/generate/source/validasi aset art konsisten + manifest + provenance/lisensi + QA raster. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/create-game-assets/SKILL.md`.
