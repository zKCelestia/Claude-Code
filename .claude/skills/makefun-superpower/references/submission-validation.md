# Submission and Validation Playbook

## 1. Pre-build rule audit

Verify:
- Required language, framework, engine, or artifact format.
- Required functionality and scope.
- Source repository requirements.
- Repository creation date and ownership restrictions.
- License requirements.
- Source bundle format and size.
- Screenshot/demo/dossier requirements.
- Transcript or agent-work evidence requirements.
- Security and secret-scanning requirements.
- Duplicate submission rules.
- Resubmission and replacement semantics.
- Quota and account-level eligibility.

## 2. Preserve provenance

For every candidate:
- Competition ID.
- Branch/worktree.
- Commit hash.
- Build command and environment.
- Bundle filename, byte size, and SHA-256.
- Screenshot/demo artifact hashes where practical.
- Validation command and complete result.
- Submission receipt and timestamp, if submitted.

Never report a validation result for a different commit or bundle as if it applied to the submission.

## 3. Validation layers

### Local validation
- Unit and integration tests.
- Build and runtime smoke tests.
- Determinism/reproducibility.
- Performance benchmarks with repeated runs.
- Accessibility/usability checks where relevant.
- Security scan and secret scan.

### Independent validation
Use a clean environment or independent machine where feasible. Record environment differences and do not overstate comparability.

### Official validation
Run the platform's official checker/CLI/API process using current documentation. Preserve the exact output.

A pass means only what the checker says it means. It does not prove the judge will award a high score.

## 4. Submission readiness gate

Before asking for authorization, provide:
- Exact intended competition and submission action.
- Exact commit and bundle hash.
- Official check results.
- Known risks and unresolved warnings.
- Current submission status and fallback.
- Current quota and `can_submit`.
- Whether the action replaces an existing entry.
- Deadline and time remaining.
- Expected benefit and downside.

Use `templates/SUBMISSION-READINESS.md`.

## 5. Resubmission risk

Treat every resubmission as potentially destructive until proven otherwise.

Investigate:
- Does the new submission replace the old one?
- Does it create a new match ladder or reset scoring?
- Is the previous score preserved?
- Does it consume a daily or hard quota?
- Does it invalidate a finalist qualification?
- Can the platform reject it after consuming quota?
- Is the new build demonstrably better?

Never gamble a valuable live entry on an unmeasured change.

## 6. Final verification

After an authorized submission:
- Verify receipt and submission ID.
- Verify status and validation.
- Verify commit and bundle identity.
- Verify leaderboard presence.
- Record claim/receipt information securely without exposing secret codes in reports.
- Update the project state.
