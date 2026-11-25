# Leaderboard and Scoring Intelligence

## 1. Distinguish the states

Do not collapse these concepts:

- **Received/submitted:** platform accepted the request or receipt.
- **Valid/compliant:** entry passed required intake/security/rule checks.
- **Scored:** one or more judging stages produced a score.
- **Ranked:** entry appears in a leaderboard population.
- **Prize-eligible:** entry meets payout eligibility filters.
- **Finalist/qualified:** entry advances to a later stage.
- **Paid/winner:** official final outcome awards a prize.

A submission can be valid but weak. It can be ranked but not prize-eligible. It can qualify for a final stage without earning a payout.

## 2. Always record the population

A rank is meaningless without its denominator and filter.

Capture separately where available:
- Total entries.
- Ranked entries.
- Judged/compliant entries.
- Prize-eligible entries.
- Finalists.

Example: rank 320 of 3,001 and rank 334 of 3,115 can both be accurate at different timestamps or under different filters. Do not "correct" one without evidence. State which source and population each represents.

## 3. Score versus rank

Score is usually more useful for understanding the gap; rank is useful for understanding relative position. Capture both.

Calculate:
- Score gap to paid cutoff.
- Rank gap to last paid position.
- Relative percentile.
- Score density around the cutoff.
- Tie-breakers.
- Rate of leaderboard movement over time.

Do not use percentile as a substitute for paid qualification. Top 10% is not top 10.

## 4. Provisional and match-based scores

If scoring uses matches or pairwise comparisons, record:
- Wins, draws, losses.
- Number of matches completed.
- Provisional/final flag.
- Opponent identities and strength, if exposed.
- Confidence interval and standard error.
- Whether all entries have equal match counts.
- Whether the score is opponent-strength-weighted.
- Whether a final stage re-scores from scratch.

Do not assume 20 wins means the best possible score if opponent strength affects the rating. Do not assume more matches are available if the platform caps the provisional ladder.

## 5. Cutoffs

There may be more than one threshold:
- Paid-placement cutoff.
- Finalist qualification cutoff.
- Shortlist cutoff.
- Eligibility threshold.

Label them separately. A project can be above the finalist cutoff and below the paid cutoff.

## 6. Dashboard/API discrepancies

When dashboard and API disagree:
1. Record both values and timestamps.
2. Check whether the API is authoritative and whether the dashboard is stale.
3. Compare population filters and status filters.
4. Check whether new entries landed between snapshots.
5. Preserve uncertainty if the exact dashboard filter is unknown.

Never silently use whichever number is more favorable.

## 7. Monitoring cadence

Increase monitoring frequency near:
- Deadline.
- Payout cutoff.
- Finalist selection.
- House/reference entry arrival.
- Final scoring stage.

Avoid excessive polling that violates platform rules or wastes resources. Use official monitoring mechanisms where available.

## 8. Required leaderboard snapshot

Use `templates/LEADERBOARD-REPORT.md`. Every snapshot must include timestamp, source, competition ID, submission ID, score, denominator, cutoff, and status.
