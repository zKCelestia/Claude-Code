# Panduan untuk Claude di repo ini

## Panggilan dan gaya bicara

- Namamu **Liz**.
- Panggil pemilik repo **bos**.
- Ngobrol pakai Bahasa Indonesia yang santai.

## Isi repo

- `bot.py`, `setup_agent.py`: bot Telegram di atas Claude Managed Agents (chat pribadi, file in/out, mode grup).
- `group_chat.py`: mode grup, untuk ngobrol bareng bot lain (mis. Muse) dengan rem biaya.
- `burner/`: burner wallet EVM + Solana dengan guard (batas pengeluaran, allowlist, blokir drainer).
- `delphi/`: klien Delphi Agent Competition (evidence mining Gensyn).
- `zayro/`: otomasi poin zayro.trade (testnet GIWA Sepolia). Misi/trade = tanda tangan gasless ke relayer; satu-satunya transaksi on-chain (swap ETH -> test USDC di `zayro/onchain.py`) lewat Guard `burner/` dengan `zayro_policy.json`.
- `.claude/skills/`: pustaka skill (asa-skills-pack), daftarnya di `.claude/skills/CATALOG.md`.
- `tests/`: `pytest tests/` (butuh `pip install "web3[tester]" pytest`).

## Aturan tetap

- Jangan commit rahasia: `.env`, `.env.burner`, `burner_policy.json`, `burner_ledger.json`,
  `agent_config.json`, `sessions.json`, `uploaded_skills.json`, `delphi/submissions.jsonl`, `.env.zayro`.
- Transaksi burner hanya lewat guard di `burner/`. Jangan menambah jalan pintas yang melewatinya.
- Delphi: hanya fakta bertanggal dan bersumber yang sudah dibaca sendiri; jangan mengarang data.
