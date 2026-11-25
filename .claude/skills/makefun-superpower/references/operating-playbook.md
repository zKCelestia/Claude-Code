# Operating Playbook

## 1. Opportunity selection

Use a portfolio view rather than treating each bounty in isolation.

### Minimum intake fields
- Competition ID and title.
- Official URL.
- Prize pool and number of paid positions.
- Deadline with timezone and UTC equivalent.
- Brief, rubric, and eligibility.
- Submission and resubmission rules.
- Current field size and competitor quality.
- Estimated build, test, and iteration time.
- Required paid services, credits, infrastructure, or human actions.
- Current quota/account restrictions.

### Priority model

Use a qualitative score or ranked list. Avoid false precision.

| Dimension | Questions |
|---|---|
| Rule fit | Can every mandatory requirement be satisfied? |
| Capability fit | Does the agent have a credible edge in the judged domain? |
| Time runway | Is there enough time to build, validate, and iterate? |
| Competitive gap | Can the leaders' visible advantage be closed? |
| Paid-placement path | Is there evidence of a realistic route to the payout band? |
| Cost | What compute, API, human, and opportunity costs are required? |
| Risk | Can work damage a stronger existing entry or consume scarce quota? |

A useful default ordering is:
1. High probability + low/moderate effort.
2. High probability + high reward.
3. Medium probability with strong upside and adequate runway.
4. Low probability/high effort only after better opportunities are covered.

The operator may override this ordering.

## 2. Rubric-first development

Create a matrix before building:

| Criterion | Requirement | Evidence judge sees | Baseline | Gap | Acceptance test | Priority |
|---|---|---|---|---|---|---|

Translate vague requirements into observable evidence. For example:
- "Good UX" → task completion, legibility, hierarchy, error states, keyboard behavior.
- "Accurate model" → out-of-sample tests, calibration, baselines, error distribution.
- "Realistic game" → responsive controls, meaningful opponents, objective loop, readable feedback.
- "Fast implementation" → benchmark suite, p50/p95, repeatability, workload coverage.

## 3. Competitor inspection

Inspect:
- Top paid positions.
- A small band just outside the payout cutoff.
- Entries with similar approach or feature set.
- Any official reference or anchor entries.

Capture screenshots and facts with timestamps. Do not assume all displayed fields are judge-visible or that screenshots expose the full implementation.

## 4. Experiment discipline

Maintain an experiment ledger:

| ID | Hypothesis | Change | Metric | Baseline | Result | Decision |
|---|---|---|---|---|---|---|

Rules:
- Change one major variable at a time when possible.
- Run enough repeats to distinguish signal from noise.
- Preserve negative and neutral results.
- Re-run the full regression suite after meaningful changes.
- Revert improvements that do not produce a measurable gain or increase risk disproportionately.

## 5. Time management

Reserve explicit time for:
- Requirements and competitor research.
- Implementation.
- Validation and bug fixing.
- Submission packaging.
- Final status verification.

Do not spend the entire deadline window coding. A technically strong entry that cannot be validated or submitted safely is not a successful outcome.

## 6. Opportunity cost and stop-loss

Stop or pivot when:
- The entry is far outside the paid band and no concrete improvement path exists.
- The platform blocks submission and there is no legitimate action to resolve it.
- The remaining time is insufficient for a meaningful rebuild and validation.
- A new iteration would risk a better live entry without enough expected gain.
- A different bounty has a clearly better probability-adjusted return.

Record the stop decision and the evidence that would justify reopening it.
