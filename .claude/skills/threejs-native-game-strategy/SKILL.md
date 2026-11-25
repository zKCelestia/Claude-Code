---
name: threejs-native-game-strategy
description: Plan, architect, build, or review games whose primary prototype/web version uses Three.js/PWA while the production mobile apps are native SwiftUI + RealityKit/Metal on iOS and Kotlin + Filament/OpenGL ES/Vulkan on Android. Use when the user asks about Three.js game development, native mobile game ports, shared game assets/data, WebGL performance, RealityKit, Metal, Filament, Android rendering, iOS/Android game architecture, or converting a web game concept into native mobile apps.
---

# Three.js Native Game Strategy

## Core Position

Treat the web game and native mobile games as related products, not as one runtime.

- Web/PWA: use Three.js for the playable prototype, marketing demo, public web version, and fast gameplay validation.
- iOS: use a SwiftUI app shell plus RealityKit for high-level 3D. Use Metal only when RealityKit cannot support required rendering, effects, or performance.
- Android: use a Kotlin app shell plus Filament first. Avoid raw OpenGL ES or Vulkan unless Filament cannot support the required gameplay/rendering style.
- Shared layer: keep assets, levels, backend APIs, economy, progression, analytics, design rules, and gameplay specs portable.

Do not recommend WebView/WKWebView as the default final mobile runtime when the user wants native mobile apps. It is acceptable as a temporary diagnostic/prototype path only when explicitly requested.

## Source Lookup

Before making framework-specific implementation decisions, inspect the local docs in `references/doc-map.md`.

Use targeted searches against the relevant `LLMs.txt` files instead of relying on memory for current APIs, loaders, platform limits, or renderer setup.

Prioritize sources:

1. Local `ai-resources/*/LLMs.txt` files.
2. Official docs when the local file is missing or stale.
3. Existing project code and scripts.

## Planning Workflow

Start by identifying the lane:

- `web`: Three.js/PWA prototype or web playable build.
- `ios`: SwiftUI plus RealityKit or Metal.
- `android`: Kotlin plus Filament or lower-level graphics.
- `shared`: asset pipeline, backend, game data, economy, analytics, QA, or release planning.

For architecture work, produce a spec before code. Cover:

- Goal and target platforms.
- Prototype scope versus native production scope.
- Shared assets and data contracts.
- Renderer choice per platform.
- Gameplay loop and state ownership.
- Asset pipeline and compression.
- Backend/API boundaries.
- Performance budgets.
- Testing and device profiling.
- Implementation sequence.

## Architecture Rules

Keep renderer-specific code behind platform boundaries.

- Do not try to convert Three.js source code directly into SwiftUI/Kotlin.
- Share data, not renderer code.
- Prefer GLB/glTF, KTX2/Basis, Draco/Meshopt where supported by the lane.
- Keep level definitions, item catalogs, economy, quests, dialogue, unlocks, and tuning values in portable JSON or server-driven config.
- Keep backend APIs platform-neutral.
- Keep analytics event names consistent across web, iOS, and Android.
- Document any platform-specific divergence instead of hiding it behind vague "same game" claims.

## Web/PWA Lane

Use Three.js for fast iteration and proof.

Default stack:

- Three.js for rendering.
- GSAP only when timeline/scroll/juice animation benefits outweigh dependency cost.
- HTML/CSS/Tailwind for menus, overlays, HUD, dialogs, and marketing pages.
- Service worker and manifest only when PWA install/offline behavior is actually needed.

Performance defaults:

- Use `GLTFLoader`.
- Add `DRACOLoader` when assets use Draco.
- Add `KTX2Loader`/Basis when texture compression is part of the pipeline.
- Cap device pixel ratio on mobile.
- Batch or instance repeated props.
- Dispose geometries, materials, textures, render targets, and listeners when scenes unload.
- Keep shader and postprocessing passes minimal until profiling proves budget.

## iOS Lane

Default to SwiftUI shell plus RealityKit.

Use SwiftUI for:

- Navigation, onboarding, settings, store screens, account, modals, leaderboards, and non-game UI.

Use RealityKit for:

- High-level 3D scene rendering.
- Entity/component-style scene content.
- Animation playback when RealityKit supports the needed asset behavior.
- Physics and interaction when adequate for the game.

Use Metal only when:

- Custom rendering is central to the game.
- RealityKit cannot support the needed shader/effect pipeline.
- Profiling shows a RealityKit bottleneck that cannot be fixed at the asset/game-design layer.

Do not start with raw Metal without a clear rendering requirement.

## Android Lane

Default to Kotlin shell plus Filament.

Use Kotlin/native Android for:

- Activity/app shell, navigation, onboarding, settings, store screens, account, leaderboards, permissions, and platform services.

Use Filament for:

- Real-time physically based 3D rendering.
- glTF 2.0 asset loading via Filament/gltfio.
- Material and lighting consistency across Android device classes.

Use OpenGL ES or Vulkan only when:

- Filament cannot support a required renderer feature.
- A lower-level custom engine is justified by profiling and product needs.
- The team accepts the extra rendering, tooling, QA, and device-compatibility cost.

## Shared Layer

Create portable contracts early:

- `assets/`: source Blender files, exported GLB/glTF, compressed textures, audio, thumbnails.
- `levels/`: level/scene definitions, spawn points, triggers, difficulty, rewards.
- `game-data/`: items, upgrades, economy, quests, achievements, tuning.
- `api/`: account, save sync, leaderboard, purchases, analytics, remote config.
- `design/`: camera rules, controls, UI states, typography, colors, motion language.
- `qa/`: target device matrix, FPS/memory/battery budgets, regression flows.

When implementing, keep names stable across platforms: level IDs, item IDs, animation clip names, analytics event names, achievement IDs, save-schema keys.

## Decision Defaults

Recommend this unless the user overrides it:

1. Build a thin Three.js/PWA vertical slice to validate fun, art direction, and performance targets.
2. Build native iOS and Android vertical slices using the same assets and game data.
3. Lock shared schemas and asset naming only after both native slices load and run on real devices.
4. Expand gameplay and content after the cross-platform loop is proven.

Escalate to lower-level rendering only after a measured bottleneck or unsupported visual requirement.

## Validation Bar

For web:

- Run build/lint/test when available.
- Test in desktop and mobile viewport.
- Check console and network errors.
- Check WebGL canvas is nonblank.
- Inspect FPS/memory where tooling allows.

For iOS:

- Build and run on Simulator at minimum.
- Prefer real-device profiling for rendering claims.
- Verify asset loading, animation playback, touch input, memory, and frame pacing.

For Android:

- Build and run on emulator at minimum.
- Prefer real-device profiling across low/mid/high devices.
- Verify asset loading, animation playback, touch input, memory, thermals, and frame pacing.

Never call the mobile app "native-performance ready" from compile-only evidence.
