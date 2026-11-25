# Safety — read before running anything

## Hard rules
1. **Never paste a seed, mnemonic, password, phrase, or private key into chat,
   logs, command arguments, or any tracked file.** The scripts here generate the
   password locally and store it in `keystore/.password` with mode `600`.
2. `keystore/` is gitignored. Never commit it. If it leaks, rotate the key.
3. **Verify official links** at `https://flop.finance/official/` before using any
   faucet, contract or claim URL. A contract/account not on that page is not official.
4. **No mainnet token exists yet.** Any site offering a FLOP mint, claim, presale or
   trade is a scam. Test/dev balances are non-tradable and worth nothing.
5. **Devnet earns nothing.** Faucet grants and devnet activity carry no airdrop
   weight. Only settled inference spend on the real Testnet counts.
6. Do not fill personal Google Forms (email, real name, Telegram ID, region) on
   behalf of another person. Those are identity fields only the owner submits.
7. Never bypass CAPTCHA, email verification, device approval or provider security.

## Phrase handling (VPS / remote agent)
Store the keystore password as a local 600 file and read it through an env var at
signing time. See `docs/MUSE-SETUP.md` for the two supported options, including the
"show phrase once → user backs up → delete phrase file, keep keystore" flow.

## Reporting
Report the **public address**, whether the faucet claim succeeded, and the tx hash.
Never report the password, phrase, seed or private key.
