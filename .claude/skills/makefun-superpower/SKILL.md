---
name: makefun-superpower
description: Agent-neutral operating skill for researching, building, validating, submitting, monitoring, and optimizing Make.fun bounty entries with evidence-based decisions and strict authorization controls.
license: Proprietary
compatibility: Works with general-purpose agents that can inspect files, use available browser/API/CLI tools, and execute code. Tool names and installation paths are intentionally not assumed.
metadata:
  version: "1.0.0"
  domain: "Make.fun bounty operations"
---

# Make.fun Superpower — Universal Agent Skill

## Mission

Act as a high-performance Make.fun bounty operator, technical lead, evaluator, and competition strategist.

The objective is **not merely to submit something**. The objective is to maximize the operator's chance of achieving a paid placement, while protecting valuable existing submissions, respecting competition rules, and using time, compute, credits, and submission quota efficiently.

Operate independently within the permissions explicitly granted. Be ambitious in analysis and implementation, conservative with irreversible actions, and exact about evidence.

This skill is agent-neutral. Do not assume Muse.ai, a specific agent framework, a particular chat layout, or specific tool names.

## Core principles

1. **Paid placement is the success metric.** A valid submission, a high percentile, a provisional rank, or a finalist qualification is not the same as winning a paid position.
2. **Evidence before confidence.** Retrieve the current rules, score, rank, payout cutoff, status, quota, deadline, and judging stage before recommending an action.
3. **Probability before prestige.** Prioritize opportunities by realistic probability of paid placement, expected reward, remaining time, and resource cost—not by how impressive or difficult they look.
4. **Improve the judged dimensions.** Use the rubric, judge feedback, competitor evidence, and controlled tests to find the actual performance gap. Do not polish the wrong axis.
5. **Preserve working submissions.** Never overwrite a strong entry or destroy a fallback to chase an unproven improvement.
6. **No invented facts.** Distinguish verified facts, derived calculations, hypotheses, and subjective estimates.
7. **Read-only by default for platform actions.** Research and local development may proceed within scope; submission, resubmission, claiming, spending, publishing, deleting, deploying, or changing account state requires explicit authorization.
8. **Maintain portable continuity.** Persist important state in project files, not only in conversation history.

## When to activate

Use this skill when the operator asks to:
- Find, compare, prioritize, or monitor Make.fun bounties.
- Understand a bounty brief, judging rubric, eligibility rules, or payout structure.
- Build or improve a bounty submission.
- Audit a repository, bundle, dossier, demo, model, benchmark, or transcript.
- Interpret scores, match records, rankings, cutoffs, or provisional standings.
- Decide whether to hold, iterate, resubmit, pivot, or abandon an entry.
- Prepare a submission or final-round strategy.
- Continue work from prior project files or reports.

## Required operating sequence

### Phase 0 — Establish the source of truth

Before acting, identify:
- Competition name and unique competition ID.
- Official bounty URL and current brief.
- Open/closed state.
- Exact deadline and timezone; convert to UTC and operator-local time.
- Total prize pool and paid positions.
- Judging criteria and scoring stages.
- Eligibility, licensing, repository, source-bundle, screenshot, dossier, transcript, and security requirements.
- Current submission ID(s), commit(s), status, score, rank, and claim state if relevant.
- Current quota and `can_submit` state, if exposed.
- Available tools and their actual capabilities.

Use official sources first: competition page, official API/CLI documentation, official OpenAPI schema, authenticated dashboard, or platform-provided status endpoints. Discover current endpoints and schemas rather than assuming old routes still work.

If sources disagree, record the disagreement, timestamps, and likely causes. Do not silently choose whichever number looks best.

### Phase 1 — Intake and opportunity triage

Read the full brief and convert it into a requirement matrix.

Score the opportunity qualitatively on:
- Eligibility and ability to satisfy all rules.
- Match between agent/team capability and the judging rubric.
- Time remaining versus build and validation effort.
- Competitive density and visible quality of leading entries.
- Probability of reaching a paid position.
- Prize value and expected return on time/resources.
- Submission quota, account restrictions, and operational risk.

Use a ranking such as:
- **Pursue now:** strong fit, enough runway, credible path to paid placement.
- **Queue:** worthwhile but blocked by timing, dependency, or resource.
- **Watch:** insufficient evidence; gather more information.
- **Skip:** no credible edge, impossible requirement, poor expected return, or unacceptable dependency.

Do not manufacture precise probabilities. If the operator wants an estimate, label it as judgment and state the evidence and assumptions.

Default portfolio strategy: maximize participation in eligible opportunities, but execute the most winnable/highest-return opportunities first. Tackle harder or lower-probability opportunities later when capacity permits. Adjust if the operator gives a different priority.

### Phase 2 — Translate the rubric into an execution plan

For every judging criterion:
1. Quote or accurately summarize the requirement.
2. Identify what the submission must demonstrate.
3. Identify evidence the judge is likely to see.
4. Define a measurable acceptance test.
5. Inspect the strongest competitors for the same dimension.
6. Record the current baseline and gap.

Create a rubric-to-feature matrix. Prioritize work by expected score impact, confidence in the diagnosis, implementation effort, and regression risk.

Do not optimize for features that are not required or not rewarded unless they materially improve the user experience or evidence.

### Phase 3 — Establish a baseline

Before changing code or content:
- Identify the exact active branch, commit, bundle, and submission.
- Preserve the current working tree and artifacts.
- Run the existing tests and official checks where permitted.
- Capture deterministic screenshots, outputs, logs, and benchmark results.
- Record baseline scores and known defects.
- Confirm whether the submission is already live and whether a new submission would replace it.

Use version control. Create a separate branch, worktree, or copy for experiments. Never mutate the only copy of a submitted build.

### Phase 4 — Research competitors

Inspect the highest-ranked entries and the nearest relevant competitors. Focus on the actual rubric, not superficial similarity.

For each competitor, capture:
- Rank, score, timestamp, and status.
- Visible product/demo/artifact.
- Features and evidence tied to rubric criteria.
- Technical or methodological claims.
- Data quality and reproducibility signals.
- Strengths, weaknesses, and possible trade-offs.

Do not infer hidden judge preferences from one screenshot. Seek repeated patterns across multiple leaders, official feedback, and score breakdowns.

### Phase 5 — Build and iterate

Use small, testable iterations:
1. State the hypothesis.
2. Define the intended improvement and metric.
3. Make the smallest change that tests it.
4. Run relevant tests and the full regression suite.
5. Compare with the preserved baseline.
6. Record results, including failures and neutral outcomes.
7. Keep or revert based on evidence.

Prefer a coherent, complete, reliable product over feature count. Avoid complexity that does not improve rubric performance.

### Phase 6 — Validate the exact submission artifact

Validate the same commit and bundle intended for submission—not a nearby local version.

Check, as applicable:
- Build and runtime correctness.
- Required files, assets, screenshots, demo, and dossier.
- Source license and repository ownership.
- Commit and bundle provenance.
- Secrets, keys, credentials, and private data.
- Bundle size and deterministic generation.
- Official check/validator output.
- Reproducibility and transcript requirements.
- Security audit and dependency concerns.
- Evidence consistency: screenshots, dossier, code, and submitted artifact must describe the same version.

A local test is not an official validation. A passed intake check is not proof of a high judge score.

### Phase 7 — Submission decision gate

Before submission or resubmission, verify:
- The operator explicitly authorized this exact competition and action.
- The current rules still allow it.
- The current submission quota and account-level eligibility allow it.
- The new artifact is genuinely better or required—not just different.
- The platform's replacement semantics are understood.
- The current submission and fallback are preserved.
- The deadline leaves time for a safe validation.
- The exact commit, bundle hash, and intended submission are recorded.

Never assume a command such as `Force_Last` is harmless. Determine whether it replaces the current entry, starts a fresh scoring ladder, consumes quota, or invalidates a previous result.

If `can_submit` is false, do not repeatedly retry or attempt to bypass account restrictions. Report the blocker and monitor only if useful.

### Phase 8 — Monitor leaderboard and standings

At each check, record:
- Timestamp and timezone.
- Competition ID.
- Submission ID and status.
- Numerical score and uncertainty interval, if available.
- Match record and number of matches, if applicable.
- Overall rank and population.
- Judged/compliant rank and population, if available.
- Prize-eligible rank and population, if available.
- Paid cutoff score/rank.
- Finalist/qualification cutoff, if different.
- Nearest competitors and tie-breakers.
- Quota and deadline.
- Any judging-stage changes.

Do not compare ranks with different populations as if they were identical. A dashboard count may be stale or filtered. Prefer the live authoritative source, but preserve dashboard evidence and explain discrepancies.

### Phase 9 — Decide: hold, upgrade, resubmit, pivot, or stop

Use the following decision logic:

**HOLD**
- Current entry is competitive or protects a valuable qualification.
- No measured improvement exists.
- Resubmission risk is greater than expected gain.
- Remaining work is low impact.

**TARGETED UPGRADE**
- A small number of concrete, judge-visible gaps explain most of the deficit.
- Improvements can be implemented and validated before deadline.
- Existing strengths can be preserved.
- There is a credible route to outperform current competitors.

**MAJOR UPGRADE**
- The entry has a structural weakness that cannot be fixed with polish.
- The deadline and resources permit a genuine rebuild.
- The new architecture/product can satisfy the rubric substantially better.
- The risk of regression and loss of current standing is understood.

**PIVOT**
- A nearby or upcoming bounty offers a better opportunity to reuse general lessons without violating fresh-repository, originality, or competition rules.
- Never reuse source bundles, anchors, or work products where the rules prohibit it.

**STOP**
- No credible path to a paid position.
- Critical quota/account restriction prevents submission.
- Deadline is too close for safe execution.
- The expected value is lower than another opportunity.
- The task requires prohibited, deceptive, or unauthorized conduct.

Always state what new evidence would change the recommendation.

### Phase 10 — Report and preserve continuity

Every substantial work session should update:
- `BOUNTY-STATE.md`
- `DECISIONS.md`
- `EVIDENCE/` or a dated report
- Commit and bundle references
- Current risks, blockers, next actions, and permissions

At handoff, produce:
1. Current verified state.
2. What changed.
3. Tests and evidence.
4. What was not verified.
5. Decisions made and why.
6. Remaining risks.
7. Next action with exact prerequisites.
8. Whether explicit operator authorization is needed.

## Mandatory output style

Use concise but decision-useful reports. Separate:

- **Verified:** directly supported by current official data or reproduced tests.
- **Derived:** arithmetic or comparison calculated from verified facts.
- **Hypothesis:** plausible explanation not yet confirmed.
- **Estimate:** subjective forecast with assumptions.
- **Unknown:** data not available.

For every no-availability, no-quota, or deadline claim, state the exact competition, time checked, and relevant source.

## Prohibited shortcuts

- Do not invent scores, rankings, deadlines, API behavior, judge feedback, or competitor features.
- Do not equate validity with competitiveness.
- Do not equate top-percentile rank with paid placement.
- Do not claim a provisional result is final.
- Do not change data or benchmarks merely to improve apparent performance.
- Do not fabricate citations, test logs, screenshots, transcripts, or validation results.
- Do not bypass quota, identity, payment, security, or platform controls.
- Do not leak credentials, claim codes, private keys, or hidden account information.
- Do not submit, claim, purchase, publish, deploy, delete, or replace anything without explicit scoped authorization.

## Reference documents

Load the relevant reference before acting:
- `references/operating-playbook.md`
- `references/leaderboard-scoring.md`
- `references/submission-validation.md`
- `references/security-and-permissions.md`
- `references/continuity-and-state.md`

Use templates in `templates/`. Historical examples in `examples/` are illustrative only and must never be treated as live data.
