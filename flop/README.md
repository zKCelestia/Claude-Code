# FLOP Network (flop.finance): catatan riset dan pemantau

Dibaca langsung 2026-11-27 dari flop.finance (/, /intro, /whitepaper, /testnet, /airdrop,
/official), docs.flop.network/networks/testnet, faucet.flop.network/chain dan /limits,
plus RPC testnet resmi. Semua yang di bawah berstatus **draft/provisional** menurut
halaman sumbernya sendiri.

## Ringkasnya

- L1 berbasis Substrate untuk *proof-of-inference*: agent AI beli inference GPU pakai $FLOP,
  miner menjalankan dan membuktikan, validator memverifikasi. Bukan EVM.
- Tanpa presale/VC. Genesis 4,4 miliar FLOP = airdrop testnet (1,2 miliar masing-masing untuk
  miner, agent, validator) + 0,8 miliar ecosystem reserve.
- **Testnet live 24 Nov 2026, tapi BELUM dinilai (unscored).** Voucher earning baru mulai di
  blok final sebuah upgrade yang akan diumumkan. Aktivitas sebelum itu **tidak dihitung dan
  tidak di-backfill**. Devnet tidak menghasilkan apa-apa.
- Fase scored direncanakan sampai sekitar 90 hari, lalu snapshot di satu blok, review list,
  dan genesis (mainnet). Tanggal mainnet/TGE belum dipastikan.

## Cara tiap peran dapat airdrop (draft)

| Peran | Butuh | Dihitung dari | Unlock |
|---|---|---|---|
| Miner | GPU 16 GB+ VRAM, hardware diattest atau lolos daftar aplikasi | FLOPs inference yang lolos verifikasi | 25% liquid, 75% terbuka 1:1 dengan earning di mainnet |
| Validator | 8+ core, 64 GB RAM, NVMe 4 TB, 1 Gbps redundan | Ranking performa testnet, kursi tetap 1,2 juta FLOP (maks 1.000) | Jadi bond, terbuka linear sekitar 10 tahun |
| Agent | DID + wallet | Compute yang dibeli di sesi settled | Hanya bisa dipakai untuk inference; tiap 3 FLOP dipakai membuka 1 FLOP |

Aturan anti-farming: banyak wallet di bawah satu kendali dihitung **satu peserta**; belanja ke
miner sendiri atau muter antar-wallet sendiri **tidak dihitung**; aktivitas palsu = hangus.
Ada batas aktivitas minimum per peran. Faucet dan sekadar memegang token tidak menghasilkan
alokasi.

## Kondisi live (cek 2026-11-27 05:01 UTC)

- RPC `https://testnet.flop.network/`: genesis cocok (`0x918abd58…cfd800`), runtime
  `flop-testnet` specVersion 1014039.
- Blok final tertahan di 222.299 sementara best block terus naik (lag lebih dari 300 blok).
  Artinya finality sedang ketinggalan atau macet. Transaksi belum final jangan dianggap beres.
- Faucet testnet: `daily_cap_reached`. Sponsor stake miner dan validator: `automatic_full`
  (kuota sponsor otomatis penuh, pendaftaran otomatis tertutup).
- Pendaftaran 50 kursi validator pertama dibuka lewat form issue GitHub
  `flop-labs/network` (lihat Testnet Operator Hub di docs.flop.network).

## Rekomendasi buat bos

1. **Jangan buru-buru farming sekarang.** Aktivitas sebelum upgrade scored tidak dihitung.
   Yang penting: tahu persis kapan blok mulai-nya diumumkan.
2. **Pilih peran sesuai modal.** Tanpa GPU/server, jalur realistis cuma *agent* (beli inference
   pakai test FLOP), dan itu hanya dihitung dari sesi settled yang independen. Kalau punya GPU
   16 GB+, jalur miner paling jelas hitungannya. Validator butuh server serius dan lolos seleksi.
3. **Satu identitas, aktivitas nyata.** Multi-wallet tidak menambah alokasi dan berisiko hangus.
4. **Waspada scam.** Akun resmi hanya yang tercantum di https://flop.finance/official/
   (X @flop_labs, YouTube, TikTok, GitHub flop-labs). Tidak ada Discord/Telegram resmi. Belum ada
   token, mint, atau claim yang sah. FLOP tidak pernah minta seed phrase atau deposit.
5. Skill `flop-hermes-devnet` di `.claude/skills/` itu untuk **devnet** (tidak dapat airdrop),
   dan tiap langkah install/enroll/paid butuh persetujuan bos (lihat NOTES-ASA.md di sana).

## Pemantau

```bash
python -m flop.watch          # laporan teks, state di flop/state.json (tidak di-commit)
python -m flop.watch --json
```

Read-only: tidak bikin wallet, tidak klaim faucet, tidak tanda tangan apa pun. Yang dicek:
genesis RPC dan faucet harus sama dengan yang diumumkan, specVersion runtime (naik berarti
upgrade, kandidat mulainya fase scored), lag finality, blok final mundur (tanda reset), status
sponsor miner/validator, dan kalimat baru berkata kunci (voucher, scored, snapshot, claim, ...)
di halaman official, testnet, airdrop, dan docs testnet.

Exit code: 0 tidak ada perubahan, 1 ada alert, 2 verifikasi gagal (genesis beda atau RPC mati).
Bisa dijalankan lewat cron, misalnya tiap 30 menit. Pengumuman di X (@flop_labs) bisa
ditambahkan ke `monitor/watchlist.json` lewat `/pantau` di bot.
