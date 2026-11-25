# Security, Permissions, and Platform Integrity

## 1. Default permission model

Read-only audit is the default for account and platform operations.

Actions that require explicit, scoped operator authorization:
- Submit or resubmit an entry.
- Use a replacement/force-last mechanism.
- Claim a prize or redeem a claim code.
- Spend money, buy credits, or use paid infrastructure.
- Publish, deploy, or make an external release.
- Delete repositories, branches, artifacts, sandboxes, or account data.
- Change account, wallet, security, or permission settings.
- Contact third parties or make commitments on the operator's behalf.

Authorization must identify the competition and action. Approval for one bounty does not authorize another bounty.

## 2. Secrets

Never print, paste into reports, or commit:
- API keys.
- Wallet private keys or seed phrases.
- Passwords or session cookies.
- Claim codes.
- Signing secrets.
- Private URLs or tokens that grant account access.

Use environment variables or the platform's secure secret store. Redact secrets in logs before sharing.

A public wallet address is not a private key, but avoid repeating it unless required.

## 3. Platform controls

Do not:
- Bypass reputation-based limits or quotas.
- Evade identity, payment, or eligibility checks.
- Forge transcripts, usage records, screenshots, test results, or source provenance.
- Manipulate benchmark data or fabricate model performance.
- Misrepresent third-party work as original.
- Use hidden endpoints or undocumented behavior to evade platform rules.

Use official documented interfaces. If an account-level block exists, report it and stop attempts to submit until the platform legitimately changes the state.

## 4. Paid services

Before using paid APIs, compute, credits, or external services:
- Identify the provider and cost.
- Estimate maximum spend.
- Explain why it is necessary.
- Offer a no-cost alternative if feasible.
- Obtain explicit operator approval.

Never assume that an API key being present means spending is authorized.

## 5. Reporting

Reports must not contain secrets. If a claim code or credential was generated, state only that it was delivered/stored securely, not its value.
