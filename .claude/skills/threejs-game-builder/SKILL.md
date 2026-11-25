---
name: threejs-game-builder
description: Build real 3D browser games with Three.js by choosing the right vocabulary, then generating a working game. Use when the user wants a 3D game, a Three.js game or scene, a browser/WebGL game, a 3D prototype, an "endless runner / FPS / tower defense / racer" in 3D, a game in a specific look (low poly, voxel, pixel, cell-shaded, isometric), a clone of a game from a screenshot, lots of objects (grass, particles, crowds) via instancing, or real physics (gravity, collisions, bouncing) in the browser. Also use to turn a vague 3D-game prompt into the precise words that produce a good result.
---

# Three.js Game Builder

Build real 3D games that run in the browser with Three.js. The core idea: **the right words produce the right game.** A vague prompt makes a generic or broken scene; naming the visual style, the genre, the engine concepts, the performance trick (instancing), and the physics library produces something that looks and plays professionally.

This skill is a **vocabulary-aware builder** — it chooses the words *and* writes the working game.

## The Five Words (operating model)

Every 3D-game request is resolved across these five word-categories before writing code. State your choices to the user, briefly, so they learn the vocabulary too.

1. **Visual style** — one word that changes the entire look: `low poly`, `voxel`, `pixel art`, `cell-shaded / toon`, `flat-shaded`, `isometric`, `wireframe`, `retro / PSX`, `realistic / PBR`, `claymation`, `neon / synthwave`. Pick one deliberately; it drives geometry, materials, lighting, and post-processing. (Full list + how each maps to Three.js: `references/vocabulary.md`.)
2. **Three.js** — the engine that runs it. Name the concepts you need in the build: camera type, materials, lights, shadows, particles, shaders, post-processing, controls, loaders. The more precisely these are named, the better the result. (API lookup: `references/resources/threejs-llms.txt`.)
3. **Screenshot → clone** — when the user has *no words* but *has an image* (a game they like), the picture is the prompt. Read the image, identify mechanics/layout/style, and rebuild it. (Workflow: `references/screenshot-to-clone.md`.)
4. **Genre name** — the genre does the work: `endless runner`, `FPS`, `tower defense`, `kart racer`, `match-3`, `idle/clicker`, `twin-stick shooter`, `platformer`, `survival`, `puzzle`. Naming the genre pulls in its expected camera, controls, loop, and spawning.
5. **The scale & realism words:**
   - **Instancing** — when the user wants *a lot of something* (grass, leaves, particles, crowds, bullets, stars): use `InstancedMesh` / instanced buffer geometry to render one shape thousands–millions of times in a single draw call. Never create thousands of separate meshes.
   - **Physics** — when things must *fall, bounce, collide, or obey gravity*, plug in a physics library; do not hand-roll physics. Default to **`cannon-es`** (simple) or **`Rapier`** (fast, WASM) for 3D; `Ammo.js` for advanced; `Matter.js` is **2D only**. (Integration patterns: `references/threejs-patterns.md`.)

## Workflow

1. **Resolve the words.** From the user's request (or screenshot), determine: visual style, genre, the Three.js features needed, whether instancing is required (many objects?), and whether physics is required (gravity/collision?). Ask at most 1–3 quick questions only for genuinely missing, high-impact choices (e.g. visual style if unspecified). Recommend a sensible default rather than dead-ending — e.g. "I'll go low poly unless you'd prefer voxel."
2. **State the build plan** in one short block: the chosen words + the core loop in a sentence. Keep it tight; this isn't a GDD. (For full game *design*, that's the `game-idea-to-gdd` skill — use it first if the user wants to plan, then build here.)
3. **Scaffold and build** a single working game (see Output). Follow the scaffold and idioms in `references/threejs-patterns.md` so you don't re-derive boilerplate.
4. **Run and iterate.** Verify it loads and runs, then refine on feedback. Swapping the visual-style word is a cheap, high-impact iteration.

## Output

**Default: a single self-contained `.html` file** that runs by opening it in a browser — Three.js loaded from a CDN via an ES-module import map. This matches "one prompt → playable in the browser." Use the canonical scaffold in `references/threejs-patterns.md` (pinned version, import map, renderer, scene, camera, light, resize handler, animation loop, dispose).

Switch to an **npm + Vite project** only when the game outgrows one file (multiple modules, asset pipeline, bundled physics WASM, TypeScript) — say why before switching.

Always:
- **Pin the Three.js version** in the import map (e.g. `three@0.184.0`); never use an unversioned "latest" URL.
- Include a **game loop** with delta-time (`requestAnimationFrame` + a clock), a **resize handler**, and a **device-pixel-ratio cap** (`Math.min(devicePixelRatio, 2)`).
- Use **`InstancedMesh`** the moment a request implies many similar objects.
- Add lightweight **controls** appropriate to the genre (orbit for viewers; keyboard/pointer-lock for FPS; swipe/lane for runners).

## Using the bundled resources

`references/resources/` holds compact API references for AI lookup — grep them for exact class names, constructors, properties, and methods instead of guessing an API. See `references/resources-index.md` for what each file is and when to use it. In short: **`threejs-llms.txt`** is the primary reference; **`gsap-llms.txt`** for tween/timeline animation and juice; **`webgl-llms.txt`** for custom shaders/low-level rendering. `filament-llms.txt` and `realitykit-llms.txt` are **native (non-browser) engines** included as bonus reference — do not use them for browser Three.js games.

When unsure of a Three.js API, look it up:

```bash
grep -i -A6 "### MeshStandardMaterial" references/resources/threejs-llms.txt
```

## Guardrails

- **Performance is a design input, not an afterthought.** Many objects → instancing. Heavy scenes → cap pixel ratio, frustum culling, merge geometry, dispose unused resources, reuse materials. A browser that freezes is a failed build.
- **Don't hand-roll physics or asset formats** — use a physics library; use Three.js loaders (GLTF) for models.
- **Verify it actually runs** before declaring it done; a Three.js game that throws on load or shows a black screen is not finished. Common causes: missing light, camera inside/behind geometry, wrong import-map path, no animation loop.
- **Keep scope honest.** A "first playable" 3D prototype is better than an unfinished epic. Offer to grow it after it runs.
- Mention free assets when models/textures are needed: Kenney.nl, Poly Pizza, Quaternius (low-poly models), ambientCG / Poly Haven (PBR textures), freesound.org (audio).

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`threejs-gltf-loading`**: Load glTF/GLB ke three.js r187 + mainkan animasi: GLTFLoader, decoder DRACO/Meshopt/KTX2, AnimationMixer cross-fade, SkeletonUtils clone. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/web-engines/threejs-gltf-loading/SKILL.md`.
- **`threejs-scene-setup`**: Setup/debug scene three.js r187: import map, Scene/Camera/Renderer, setAnimationLoop + Timer, resize, OrbitControls, WebGPURenderer. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/web-engines/threejs-scene-setup/SKILL.md`.
