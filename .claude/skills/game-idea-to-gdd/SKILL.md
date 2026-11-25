---
name: game-idea-to-gdd
description: Turn rough game ideas, reference games, or "think before coding" requests into clear, right-sized Game Design Documents. Use when the user says they have a game idea, wants help planning a game, asks for a GDD/game design document, asks to think through a game before coding, wants missing game systems identified, or needs a scope/risk review for gameplay, player experience, backend, monetization, analytics, launch, or technical planning. Adapts depth to the user: a light one-page plan plus a concrete first project for beginners and solo devs; a full production GDD for experienced devs and teams.
---

# Game Idea to GDD

Guide game planning before implementation, then hand off cleanly to building. Produce a Game Design Document (GDD) sized to the user, not a fixed mega-document.

## Use when / Do not use when

Use this skill when the user is **planning a new game or a new major feature** and wants a design before code.

Do **not** run the cold-start question flow for these — switch behavior instead:

- **User already has a GDD or design doc** → enter Revision Mode (see below). Ask to load it; do not re-interrogate from scratch.
- **User has a game already in progress / shipped** → gap-check or plan the specific change; skip Question 1.
- **User wants quick brainstorming / "just give me ideas"** → offer a lighter idea-generation pass, not a 30-section GDD.
- **User wants in-engine coding help** ("fix this jump", "why does collision fail") → that is implementation, not planning. Help directly.

## Core Behavior

Do not start coding, picking a stack, or creating production assets until the user approves a concept/GDD/spec. The one exception is the post-approval handoff (see "After approval").

**Adapt to the user.** Read who you are talking to from their idea and answers:

- **Beginner / solo / game-jam dev** → plain language, explain unfamiliar terms inline (pair the key English term so they can search it, and mirror the user's language if they write in another language), recommend a small scope, produce a one-page or reduced GDD, and point them to `references/first-project-walkthrough.md` for something concrete to build.
- **Experienced dev / studio / team** → full production tone, the complete template, deeper systems (economy math, risk register, technical design).

When the user is unsure or keeps answering "I don't know" / "none of these", switch from asking to **proposing**: recommend a sensible default with a one-sentence reason, and let them confirm or adjust. Briefly explain the concept a question is probing if it seems unfamiliar. Never dead-end a beginner with a question they can't answer.

## Step 0 — Intake (always do this first)

Before asking anything, read the user's opening message and **harvest what they already gave you**. A one-line idea still contains genre, fantasy, platform, and reference hints.

1. Restate the idea in one or two sentences.
2. List **Known** (what the user already specified) and **Unknown** (genuine gaps) across the planning topics.
3. Ask questions **only about the unknowns**. Never re-ask something the user already stated.
4. If little is missing, skip questioning and produce a concept brief or v0 GDD draft (with assumptions labeled) for approval.

## Question Flow

Ask focused questions to fill the unknowns. Use the host's native multiple-choice question UI when available; otherwise present labeled options in text.

- Prefer **multiple-choice with 2–5 labeled options** when the answer space is categorical (genre, platform, art direction).
- Use **free-text or a numeric/range prompt** when the answer is creative, a name, or a number (one-sentence pitch, player fantasy, art mood, target FPS, price point, level count).
- Use **multi-select** when several answers can be true at once (platforms, input methods, monetization).
- Use a **2-option confirm** when only two answers are real.
- **Never pad with filler options** to hit a fixed count, and never truncate a longer real option set down to four — list the real options or offer "Other (specify)".

Number questions sequentially (Question 1, Question 2, …). Do **not** show a fixed denominator like "1/10" — there is no quota. Aim to reach a draft in roughly **5–8 questions**; stop as soon as the concept is clear, and keep going past that only if the user wants more depth. Each question should build on the previous answer.

Good opener (only if references are unknown): ask which existing games are closest, or — if the user has a strong mechanic but no reference in mind — ask them to describe the core action instead.

**Expert fast-path:** if the user pastes a complete concept, or says "skip the questions / just draft it", go straight to a v0 GDD with labeled assumptions and let them correct it.

**If you reach a natural limit and scope is still unclear:** produce a v0 GDD with the open questions listed as "TBD / Open Questions" rather than asking indefinitely.

## Planning Order

Plan roughly in this order, but skip topics already known and don't force irrelevant ones:

1. References, genre, and the core promise to the player
2. Target player and player fantasy
3. Core gameplay loop and primary verbs
4. Mechanics, controls, win/lose, and progression
5. Content, levels, and (if relevant) story
6. Art, animation, audio, game feel, UI/HUD, and onboarding
7. Data/save, and (only if relevant) backend, online, analytics, monetization, launch
8. Performance and platform constraints
9. Technical architecture and the runtime loop — only after gameplay and scope are clear
10. Scope cut line, risks, milestones, and how it will be tested and balanced

Delay frontend/backend/database/API stack decisions until gameplay, platform, and scope are clear.

## Writing the GDD — depth, not labels

This is the most important rule for output quality. The template is a list of topics; your job is to fill each with **decisions, not labels**.

- Every section gets **prose or a table, not a single phrase**. A section that just says "Scoring: points" is a failure.
- For each design decision, state **the choice, the reason, and one concrete example or number.**
- Aim for decisions a developer could build from. "Difficulty increases" is a label; "enemy spawn rate rises 15% per level, capped at level 10" is a decision.
- Match length to the user: a beginner's one-page GDD still states real decisions; it just covers fewer sections.

Example of the target depth, for Core Loop: *"Player swipes to switch lanes (verb); coins and a rising combo meter reward clean dodges (reward); one hit ends the run and banks coins for upgrades (reset). A run lasts ~60–90s."* — verb, feedback, reward, and reset, with a number.

## Outputs

The first major output is a GDD outline or draft, **not code**. Default outputs:

- Concise concept brief
- Concept pitch / one-pager (high-concept artifact)
- Full or right-sized GDD draft
- Missing-systems review and scope/risk review
- Prototype milestone plan and first-task list
- Implementation steps **after** user approval

**Artifact contract:** write the GDD to a markdown file by default (e.g. `docs/gdd.md`, or named after the working title) so it persists and can be revised, and confirm the path with the user. On later passes, **edit that file** rather than reprinting the whole thing in chat. Reprint inline only on request.

**Coverage:** a full GDD covers the sections in `references/gdd-template.md` — that file is the single source of truth for structure. Include conditional sections (story, backend, online, monetization/marketing, analytics, economy, security/privacy) only when in scope. **Mark inapplicable sections "N/A" with a one-line reason** rather than padding them with filler — that is how GDDs become bloated and unread.

When producing or finishing a GDD, read `references/gdd-template.md` and follow its structure and per-section guidance.

During the question phase, or when pressure-testing an idea for missing systems or running a scope/risk pass, read `references/game-thinking-checklist.md`.

When the user is a beginner, asks what to build first, or has no references, point them to `references/first-project-walkthrough.md`.

## Consistency pass (before presenting any GDD)

Before declaring a GDD ready, reconcile it against itself and flag any mismatch:

- Platform ↔ controls ↔ UI agree (e.g. touch-only implies mobile and gesture UI).
- Online features (leaderboards, multiplayer) imply backend auth and anti-cheat.
- Monetization (IAP) implies purchase validation, save integrity, and a supporting economy.
- Scope ↔ milestones agree (the cut line matches what's in "first playable").

## Revision Mode

If a GDD already exists (in chat or a file), do not restart the funnel:

1. Load it.
2. Ask what changed (targeted questions only — the question budget does not apply).
3. Edit only the affected sections.
4. Re-run the relevant checklist sections against the touched areas **and their dependents** — e.g. switching from premium to F2P reopens Economy, Monetization, Analytics, and Security.

## After approval — handoff

The "no coding" gate exists to be released. **Approval** = the user says the GDD/spec is good enough to build.

On approval:

1. State the first-playable scope and produce a concrete **3–7 task implementation list**.
2. For beginners, tie the first task to `references/first-project-walkthrough.md`.
3. Explicitly lift the coding gate and proceed to building when asked.

If the user asks to code immediately at the start, don't refuse — confirm scope in one question, produce a one-page spec, then proceed.

## Guardrails

- If information is missing, ask the next best question; if the user wants no more questions, create a v0 GDD with clearly labeled assumptions, following `references/gdd-template.md`.
- If the idea is too large for the user's likely resources, surface a smaller first-playable scope before discussing full production.
- If backend, accounts, purchases, multiplayer, analytics, anti-cheat, or admin tools appear in scope, include security and privacy considerations.
- End each planning pass with either the next single question, or a clear GDD/spec ready for approval.

## V3 enrichment — game-design-systems (Ultimate Agent Skills V3, 2026-11-20)

### Loop, ekonomi & balancing

This section *operationalizes* what the GDD already sketches — it does not redefine it. `references/gdd-template.md` §5 (Core Gameplay Loop), §8 (Progression), and §9 (Economy & Progression Math, incl. the currency sources/sinks table) plus `references/game-thinking-checklist.md` (Core Loop, Progression, Economy) already ask the right questions; the workflow below turns those answers into simulated, measured balance:

- **Gameplay loop:** state the audience and the loop at three scales — moment-to-moment (seconds), session (minutes), meta-progression (across sessions) — with verb, feedback, reward, and reset, each with a number.
- **Model economy sources/sinks:** turn the §9 currency table into a quantitative model — every faucet (sources) and drain (sinks) with rates, so total daily faucet can be checked against the cheapest meaningful sink.
- **Prototype & simulate progression:** simulate the progression curve (XP/level formula, upgrade costs, time-to-goal) instead of asserting it; a curve that looks fine in prose often breaks at level 20.
- **Tune against playtest evidence:** change one variable per iteration, playtest, and record the observed result — the checklist's "which single variable changes per balance iteration?" is the rule here.

Deliverables: GDD sections §5/§8/§9 filled with decisions and numbers, data tables (currency, XP curve, upgrade costs), and balance tests (simulated runs + playtest notes).

Related skills: `threejs-game-builder` (turning the designed vocabulary into a real game).

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/game-design-systems/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — ringkasan skill upstream gamedev yang tumpang tindih

Sumber: gamedev-skills/awesome-gamedev-agent-skills @ c6ca6c41 (Apache-2.0).

Skill upstream berikut tumpang tindih dengan skill ini — terdaftar reference-only
di registry (JANGAN duplikat sebagai direktori baru). Ringkasan metode + sumbernya:

- **`game-docs`**: Tulis & rawat design doc game: GDD satu halaman + indeks fitur + catatan fitur, disinkronkan ke kode lewat link/status checker (`check_docs.py`). File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/workflows/game-docs/SKILL.md`.
- **`game-jam`**: Rencanakan & kirim entry game jam dengan deadline tetap: baca aturan jam, scoping ke jam, cut list, cek build sebelum submit. File lengkap: `~/workspace/ultimate-agent-v3/vendor/gamedev/skills/workflows/game-jam/SKILL.md`.
