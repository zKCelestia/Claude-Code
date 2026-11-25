# Historical Case Study: Token Radar

**Snapshot:** 15 November 2026, approximately 12:35 WIB.  
**Competition:** `token-radar-01` — Build the best token launch radar.  
**Purpose:** Demonstrate evidence-based leaderboard and competitor analysis. These figures are historical, not live.

## Verified state at the snapshot

- Active entry was scored and passed round-one validity checks.
- Judge win rate: **0.934805**.
- 90% interval: **[0.917708, 0.951903]**.
- Record: **20 wins, 0 draws, 0 losses in 20 matches**.
- Live API rank: **#334 of 3,115 entries** (3,113 ranked).
- Account dashboard had earlier shown #320 of 3,001; the two snapshots differed in timestamp/population.
- Top-10 cutoff: **0.954756**.
- Score gap to cutoff: approximately **0.019951**.
- Per-criterion judge breakdown was unavailable until the deadline; claims about hidden criterion scores would have been invented.

## Competitive finding

The submitted log-log value curve was materially the same as the curve visible in the #1 competitor's artifact. The differentiators were features layered on top:

1. **Net farming economics:** leaders displayed estimated return, net dollars per hour, cost/time/net columns, and FARM/THIN/SKIP decisions. Our plan listed costs and time but did not estimate what the farming was worth.
2. **Calibration evidence above the fold:** leaders showed blind-test errors and calibration visuals prominently. Our LOO evidence was buried in the methodology section.
3. **Category/family adjustment:** some leaders applied category or sibling shifts. Our model applied no shift for categories with fewer than three live comparables.
4. **Coverage presentation:** leaders exposed self-check badges, family/tier views, and more complete live-token views.

## Verified technical audit

- Re-running the submitted commit reproduced the board output.
- 198 rankable protocol rows matched the independent recount.
- LOO median absolute log error was approximately 1.163, better than the tested category-median and TVL-only baselines.
- The detail-view rounding issue mentioned in an older draft was absent in the submitted version.

## Decision lesson

A targeted upgrade was recommended:
1. Add explicitly assumption-labelled net farming economics.
2. Add cautious hierarchical category shifts with out-of-sample revalidation.
3. Move calibration evidence above the fold.
4. Show the full live set and add a computed self-check badge.

The case demonstrates that a good core model can still lose because the product does not expose decision-useful outputs or competitive evidence clearly.

## Safety lesson

Do not copy an extreme competitor assumption merely because it produces an attractive ranking. A 400x comparable outlier should be treated carefully, with robust residual handling and transparent uncertainty—not imported wholesale.
