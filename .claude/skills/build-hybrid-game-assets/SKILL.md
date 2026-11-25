---
name: build-hybrid-game-assets
description: Plan, create, integrate, or audit a hybrid asset pipeline for a Three.js or web game. Use when choosing among imported meshes, procedural 3D geometry, AI-generated reference art, 2D UI media, sprites, VFX, and performance-ready runtime asset delivery.
---

# Build Hybrid Game Assets

Choose the asset representation that best serves gameplay, readability, iteration speed, and runtime budget. Do not force every reference image through image-to-3D reconstruction.

## Classify the asset before making it

| Need | Preferred representation |
| --- | --- |
| Hero character or complex authored animation | Imported rigged mesh, with verified license and scale |
| Weapon, relic, pickup, creature variant, architecture, or interaction prop | Procedural Three.js geometry when controllable silhouette, sockets, collision, or code-driven variants matter |
| Concept, class portrait, inventory icon, cursor, backdrop, or menu treatment | Generated or authored 2D image/video used directly as UI media |
| Level mood, composition, or spacing reference | Concept image used as visual guidance; author the actual playable level separately |
| Reference image whose visible form itself must become a code model | Use `img2threejs` with its quality gates and state the result is a reconstruction, not extracted geometry |

## Create image-first work accurately

Generate a compact reference set: hero view, silhouette/side view when geometry matters, palette/material close-up, and usage context. Define camera distance, scale, pivot, collision, attachment sockets, animation needs, and budget before implementation. A single image cannot establish hidden geometry; request more views or select deliberate stylization.

## Build the runtime asset

- For imported meshes, normalize coordinate system, scale, pivot, materials, animation clips, and ownership/license before scene integration.
- For procedural geometry, expose a factory with named parts, stable sockets, deterministic variation, collider guidance, and reusable materials.
- For 2D assets, export transparent media at the actual display density; provide alt text/labels where user-facing and avoid using raster art as fake 3D collision.
- Keep authored content identifiers separate from runtime state. Do not duplicate item, material, or gameplay facts in UI code.

## Verify in the game, not the asset viewer

Check the real camera distance, lighting, readability, collision/contact, animation, mobile viewport, and performance. Measure representative draw calls, triangles, texture count, and frame time. Keep visuals original: use references for visual grammar, then create new identity, geometry, and media.

## Record provenance

Track whether each runtime asset is imported, procedural, generated 2D, or reference-only, together with source/license and generation input where applicable. Do not claim an image-to-model pipeline unless source and runtime code actually demonstrate one.

## V3 enrichment — asset-2d-ui, asset-local-ai, game-asset-pipeline (Ultimate Agent Skills V3, 2026-11-20)

This skill already decides *which* asset representation to use. The three sub-sections below add the production workflows that decision implies — 2D production, local-AI production, and the brief/budget/provenance discipline that governs all of them. Nothing above is changed.

### Asset 2D & UI production (dari `asset-2d-ui`)

Production workflow for sprite sheets, pixel art, icons, and vector UI — the representation this skill already classifies as "generated or authored 2D image/video used directly as UI media":

- **Sprite sheet & pixel art:** specify palette, grid, padding, and sizes before drawing; keep a consistent grid so frames slice cleanly.
- **Atlas + metadata export:** export the atlas together with its metadata (frame bounds, pivot, names) — the atlas without metadata is not a deliverable.
- **Icons / vector UI:** keep icon styles consistent (stroke, palette, corner radius); prefer vector sources so one asset scales to all densities.
- **Check scaling & transparency:** verify at the actual display density and against light and dark backgrounds; transparent edges must not show halos or premultiplication fringes.

Tooling (production): Krita, LibreSprite, Pixelorama, Inkscape.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/asset-2d-ui/SKILL.md

### AI lokal — tanpa API berbayar (dari `asset-local-ai`)

Concrete workflow for the "AI-generated reference art" representation this skill already names — kept local and license-clean:

- **Check licenses & resources first:** model license and output license, plus local compute (VRAM/disk) — if either is unclear, do not generate.
- **Use approved local workflows only:** ComfyUI, TripoSR (and Blender for cleanup) — no paid API, no external upload without explicit permission.
- **Clean the output manually or procedurally:** AI output is a candidate, not a finished asset; fix hands, seams, topology, and stray geometry before it enters the pipeline.
- **Verify actual engine import:** a pretty render is not proof — import the mesh/image into the target engine and check transform, materials, and scale.

Related skills: `meshy-image-to-glb`, `img2threejs`.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/asset-local-ai/SKILL.md

### Brief, budget & provenance (dari `game-asset-pipeline`)

The governing discipline for every asset, applied before production starts:

- **Asset brief + style guide first:** art style, engine, dimensions, scale, performance target, polycount/texture budgets, and needed formats — written down before any asset is made.
- **Budget defined up front:** polycount, texture resolution/format, and the performance target each asset must meet; compress only after comparing quality and measuring against the budget.
- **Manifest provenance:** record URL, creator, license, modifications, and attribution for every asset. Reject assets with unknown rights, ripped commercial content, or dependencies that require payment.
- **Tooling rules:** run approved local Blender scripts or reviewed MCP functions only, inside project scope. Avoid external uploads and paid model calls unless explicitly authorized. Never install or run unknown code silently.

Related skills: `blender-game-3d` (canonical Blender flow — the executor for this brief), `threejs-asset-pipeline` (optimization + validation of the output).

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/game-asset-pipeline/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`create-game-assets`**: Rencanakan/generate/source/validasi aset art konsisten + manifest + provenance/lisensi + QA raster. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/disciplines/create-game-assets/SKILL.md`.
