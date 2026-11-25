---
name: crypto-airdrop-prep
description: Use when researching or preparing for a crypto airdrop.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [crypto, airdrop, testnet, did, eligibility]
---

# Crypto airdrop prep

## When to Use
Use when the user asks to "garap airdrop", prepare for a testnet/farming program, or sets up an agent DID for an airdrop. Goal: determine whether the program is real and what actually earns weight BEFORE spending time or money, then prepare identity safely.

## Procedure
1. **Verify official surfaces first.** Open the project's own `/official` or links page. Treat only listed domains/accounts as real; there is no legitimate Discord/Telegram if the official page says so. Record the exact official X handle and docs URL.
2. **Read the status, not the marketing.** Check the airdrop page and the network/testnet status page. Distinguish `planned` / `target` / `live`. A target date is not a launch. Development networks frequently earn nothing — read the FAQ line that says whether devnet activity carries airdrop weight.
3. **Identify the earning mechanism.** Airdrops described as "earned, not given" pay for verified work (compute served, settled inference spend, stake at cutover), not for holding, registering, or creating an identity key. State plainly which action creates a claim.
4. **Check for an existing token.** If the docs say no mainnet token exists, say so explicitly: any mint/claim/trading site is a scam. Never interact with a "claim" contract that is not on the official page.
5. **Prepare identity without exposing secrets.** Generate the agent DID/key with the project's official CLI into an **encrypted keystore** with a locally generated password in a 600 file. Report the public address only. Never print seed, mnemonic, password, or private key into chat or logs.
6. **Set up monitoring, not premature action.** Offer a watcher on the official status page that reports when status actually flips from planned to live. Do not claim faucet funds or submit work on devnet and call it airdrop progress.
7. **Execute an explicit claim request through the faucet's own UI.** When the user directly asks to claim, prefer the faucet web UI over the CLI: fetch the faucet page and its JS, identify the address input / claim button / POST payload shape, then drive it with headless Chrome (puppeteer-core + a local Chromium binary) — fill the public address, click the claim button, wait for the result element, and report the success text plus tx hash. The web server performs its own chain-identity check, so this path still works when the CLI's RPC genesis preflight is failing. Install puppeteer-core in the task's own working directory, not in another project's folder that may be deleted.
8. **Report in the user's style.** Indonesian, "bro", short, status first: what is confirmed live, what is still a target, what the earning action is, what is prepared locally. No long process narration.

## Always-on rules
- Never ask the user for seed phrases, private keys, or wallet passwords in chat.
- Do not fill personal Google Forms (email, real name, Telegram ID, region) on the user's behalf — those are identity fields only the user submits.
- Never claim airdrop eligibility from registering interest, creating a DID, or holding a faucet grant if the docs say those earn nothing.
- Separate the user's own tools from the airdrop workflow; do not start or stop unrelated services as part of this task.
- State a caveat once, then act when the user explicitly asks. If the user says they already checked something, do not keep re-asserting the opposite conclusion — acknowledge and proceed with the requested action unless a concrete safety gate blocks it.

## Pitfalls
- A public RPC probe via HTTPS can return 405 while the WebSocket endpoint is perfectly healthy. Verify a WS method call (`system_chain`) before reporting the network unreachable.
- An official CLI can time out on its own health probe once, while a direct WS call succeeds. Treat a single timeout as transient; confirm with a second method before escalating.
- Faucet health may report signer connectivity rather than grant readiness; check indexer lag and funding status separately.
- A CLI claim can fail on its own RPC preflight while the faucet web UI is healthy — the CLI compares RPC and faucet genesis before funding, so a WS timeout or 503 blocks it even though the faucet's `/fund` endpoint is fine. Drive the web UI instead of retrying the CLI indefinitely.
- Registering a DID can be described as a "day-one requirement" while the same FAQ says creating DIDs earns nothing — both are true: prepare it, but do not present it as progress toward the airdrop.

## Verification
A correct prep session ends with: official links recorded, status correctly labeled planned vs live, earning action identified, encrypted keystore + public address reported, secrets never shown, and any monitoring actually scheduled. Do not claim the airdrop was "farmed" when the testnet has not opened.
