# Cross-Agent Continuity and State Management

## 1. Do not rely on chat history

A bounty project must remain understandable if:
- The agent changes.
- The conversation is moved.
- A session expires.
- A different tool runtime takes over.
- The operator opens a new chat or workspace.

Use files as the durable source of project state.

## 2. Recommended files

- `BOUNTY-STATE.md` — current verified facts and next actions.
- `DECISIONS.md` — decisions, rationale, authorization scope, and reversals.
- `EVIDENCE/` — dated screenshots, API outputs, test logs, official checks.
- `reports/` — human-readable audit and leaderboard reports.
- `experiments/` — hypotheses, variants, results, and benchmark comparisons.
- `SUBMISSIONS.md` — submission IDs, commit hashes, bundle hashes, status, receipts (never claim codes or secrets).

## 3. State update discipline

After meaningful work:
1. Update current facts with timestamps.
2. Mark stale facts as historical.
3. Add new decisions; do not erase prior decisions.
4. Preserve evidence for failed experiments.
5. Record the exact next action and approval required.
6. State what has not been verified.

## 4. Handoff format

A handoff must answer:
- What is the goal?
- What is the current active submission?
- What is the latest verified score/rank/status?
- What changed since the last snapshot?
- What has been tested?
- What remains uncertain?
- What is blocked?
- What is the next best action?
- Which actions require operator approval?

Use `templates/BOUNTY-STATE.md`.
