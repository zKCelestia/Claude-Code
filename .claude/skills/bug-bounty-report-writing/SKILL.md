---
name: bug-bounty-report-writing
description: Write bug bounty reports that get triaged quickly and rated accurately — clear impact statements, minimal reproduction steps, and professional tone. Use before submitting any vulnerability report.
---

# Bug Bounty Report Writing

Turn findings into reports that triagers accept quickly and rate fairly.

## Report Structure

1. **Title** — vulnerability class + affected asset. `Stored XSS in ticket comment field on support.example.com`
2. **Severity & CVSS** — your suggested rating with vector string
3. **Summary** — 2–3 sentences: what, where, impact
4. **Steps to Reproduce** — numbered, copy-pasteable, no assumptions
5. **Impact** — what an attacker gains, concretely
6. **Supporting Material** — HTTP requests/responses, screenshots with sensitive data redacted
7. **Remediation** — specific fix recommendation

## Rules

- One vulnerability per report. Chains go in one report only when each step is meaningless alone.
- Impact must be demonstrated or rigorously argued, not speculated. "Could lead to RCE" without a path gets downgraded.
- Redact personal data in evidence. Blur user PII; never include other users' data you accessed — report the access, delete the data.
- No markdown-breaking formatting in pasted logs; use fenced code blocks.
- Write for a triager seeing the asset for the first time.

## Common Downgrade Causes to Avoid

- Self-XSS or XSS requiring victim-installed software presented as high severity
- Missing `Content-Security-Policy` or verbose headers with no demonstrated exploit
- Theoretical IDOR without showing two distinct accounts affected
- Automated scanner output pasted without manual verification

## After Submission

- Respond to triager questions within the program's SLA
- Request re-review only after substantive new information
- Do not disclose publicly until the program's disclosure policy allows
