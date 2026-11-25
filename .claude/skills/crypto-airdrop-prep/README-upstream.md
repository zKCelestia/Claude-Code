# FLOP Airdrop Kit (public)

Public, reusable tooling for preparing a FLOP Network agent identity and claiming
devnet faucet grants through the **browser UI** (the same way a human does).

**No secrets, no personal data, no real addresses are included in this repo.**
Every agent generates its own keystore locally. See `docs/SAFETY.md`.

> Devnet faucet grants carry **no airdrop weight**. Airdrop is earned by settled
> inference spend on the real Testnet. Verify status before relying on any date.

## What's inside

| Path | Purpose |
|---|---|
| `skills/crypto-airdrop-prep/SKILL.md` | Agent skill: verify official surfaces, status, earning mechanism, safe identity prep |
| `skills/flop-hermes-devnet/SKILL.md` | Agent skill: install/configure native Hermes provider on FLOP devnet + readiness checks |
| `scripts/setup-identity.cjs` | Generate an encrypted agent keystore + locally generated password (600 files) |
| `scripts/faucet-claim-browser.cjs` | Claim test FLOP via the faucet **web UI** with Puppeteer (no CLI/API RPC probe) |
| `docs/MUSE-SETUP.md` | Two options for Muse/personal-agent setups, incl. phrase handling & deletion |
| `docs/SAFETY.md` | Hard rules: secrets, official links, devnet vs testnet, scam warnings |

## Quick start (agent on a VPS)

```sh
npm install puppeteer-core
CHROME_PATH=/path/to/chrome node scripts/setup-identity.cjs my-agent
# -> keystore/agent.json (600), keystore/.password (600). PUBLIC address printed only.
CHROME_PATH=/path/to/chrome node scripts/faucet-claim-browser.cjs <YOUR_PUBLIC_SS58>
# -> opens faucet, fills #addr, clicks grant, prints result
```

## Official surfaces (verify again before use)
- Website / airdrop / official links: `https://flop.finance/`, `/airdrop/`, `/official/`
- Docs: `https://docs.flop.network` and `https://ask.flop.finance`
- Faucet: `https://faucet.flop.network` (devnet)
- X: `@flop_labs`

This repo is unofficial tooling. Verify every URL against `https://flop.finance/official/`.
