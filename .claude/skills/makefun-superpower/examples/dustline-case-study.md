# Historical Case Study: DUSTLINE / Three.js Tactical FPS

**Snapshot:** 15 November 2026, approximately 12:34 WIB.  
**Competition:** `threejs-fps-02`.  
**Purpose:** Demonstrate rubric diagnosis, quota-aware decisions, and pivot strategy. These figures are historical.

## Verified state at the snapshot

- V3 was valid; sealed scorer passed 5/5.
- Dev win rate: **0.770565**.
- 90% interval: **[0.731574, 0.809556]**.
- Record: **3 wins, 0 draws, 9 losses in 12 matches**.
- Live API rank: **#412 of 2,182 rows**.
- Prize-eligible rank: **407 of 1,823**.
- Top-10 cutoff: **0.943605**.
- Score gap: **0.173040**.
- The account quota endpoint reported `can_submit: false` due to an account-reputation restriction, despite apparent numeric quota remaining.

## Judge-feedback diagnosis

The nine losses were repeatedly against two stronger opponents. The judge's reasons identified three major gaps, in priority order:

1. **Gunplay depth:** missing ADS/zoom, bloom model, recoil pattern, sniper rifle, and walk key.
2. **Tactical depth:** missing A* waypoint navigation, hearing bus, angle-holding/peeking bots, droppable bomb, additional bomb site rotation, richer grenade behavior, callouts, and full scoreboard.
3. **Code architecture:** a large monolithic game file versus fixed-step simulation, modular systems, and pooled effects.

The visual presentation was often described as richer or prettier. The lesson: V3 improved the wrong axis. Visual polish could not compensate for missing gameplay depth and architecture.

## Decision lesson

A V4 in the same competition was not recommended as the default:
- The score gap was very large.
- A major rebuild, not a cosmetic pass, was needed.
- The account-level submission block meant a completed V4 could not currently be submitted.
- The deadline was close.

A nearby new FPS bounty was identified as a possible pivot, but it required a fresh repository and fresh anchor; the old source/bundle could not simply be reused where the new rules prohibited it.

## General lesson

When a judge repeatedly identifies the same weaknesses, treat that feedback as a diagnosis. Do not spend the remaining time polishing screenshots while the primary rubric dimensions remain weak. If quota/account restrictions block submission, do not attempt to bypass them.
