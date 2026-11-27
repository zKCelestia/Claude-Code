# FLOP Testnet: runbook peran Agent

Disusun 2026-11-27 dari bahan yang dibaca langsung: https://flop.network/llms.txt,
docs.flop.network (testnet FAQ), gateway `https://gateway.testnet.flop.network` (`/health`,
`/v1/models`, `/openapi.json`), faucet `https://faucet.flop.network` (`/chain`, `/limits`), dan
README + CHANGELOG paket npm `@flop-labs/cli` 0.10.3 / `@flop-labs/sdk` 0.13.1 (dibaca, belum
dijalankan). Panduan miner-pin di ask.flop.finance masih berlabel **devnet**, jadi bagian
`session run` di bawah perlu dikonfirmasi ulang untuk testnet.

## Wallet agent bos

- Alamat testnet: `5FbXs9twtnVtSTweiFiYW3phbBTmZKnR1azMG77WjUhhyCx1` (sr25519, SS58 42).
- Dibuat 2026-11-27 di sesi Claude dan diverifikasi dengan @polkadot/keyring (format Polkadot JSON
  v3, scrypt + xsalsa20-poly1305). Keystore dan password dipegang bos dan **tidak ada di repo**.
- Saldo awal 0, nonce 0. Belum ada klaim faucet (saat itu `daily_cap_reached`).
- Sesi berikutnya: bos upload `flop-agent-testnet.json` (password terpisah) ke sesi, lalu lanjut.
  Jangan bikin wallet baru: satu identitas = satu peserta.

## Cara agent dihitung (draft airdrop)

- Pool agent 1,2 miliar FLOP, dibagi **pro rata compute yang dibeli di sesi settled**.
- Faucet dan memegang token tidak menghasilkan alokasi. Ada batas aktivitas minimum.
- Belanja ke miner milik sendiri atau muter antar-wallet sendiri **tidak dihitung**. Banyak
  wallet di bawah satu kendali dihitung satu peserta.
- Alokasi agent terkunci: hanya bisa dipakai untuk inference, tiap 3 FLOP dipakai membuka 1 FLOP.
- **Sekarang belum dihitung.** Hitungan mulai di blok aktivasi upgrade yang akan diumumkan
  (belum ada tanggal). Aktivitas sebelum itu nol, tanpa backfill.

## Kondisi testnet (cek 2026-11-27 ~05:05 UTC)

- Gateway testnet live (`/health` ok, genesis cocok). Model: `qwen/qwen3-14b` dan `qwen/qwen3-8b`,
  masing-masing dengan beberapa miner di `price_sources`.
- Harga: `flop_per_gn` 0,00000002 × 30 gn/token (14B) = sekitar 0,0000006 FLOP per token. Jadi 10
  FLOP faucet itu sangat banyak. Yang menentukan biaya sebenarnya adalah **escrow** (`--max-flop`):
  cooperative close membayar seluruh escrow ke miner, dan sisa yang tidak terpakai tidak
  dikembalikan. Biaya transaksi dihitung terpisah.
- Pendaftaran kunci gateway testnet (`/v1/enroll/wallet/challenge`) menjawab 404, artinya
  **dimatikan**. Jalur API-key lewat gateway belum bisa dipakai.
- Faucet: klaim agent 10 FLOP per wallet per 24 jam (rolling). Grant berikutnya butuh grant
  sebelumnya **sudah dipakai** on-chain (`rolloverRequiresSpend`). Saat dicek, status
  `daily_cap_reached` (kuota harian faucet habis).
- Runtime testnet specVersion 1014039. CLI 0.10.1+ sudah siap untuk 1014040, jadi upgrade itu
  kemungkinan dekat. `python -m flop.watch` akan memberi alert saat itu terjadi.

## Temuan setelah bedah CLI 0.10.3 (2026-11-27 ~05:30 UTC)

- `flop keys generate` defaultnya **ed25519**, sedangkan agent harus `--type sr25519`. Mnemonic
  tidak ditampilkan (kecuali `--show-secret`), jadi backup-nya adalah file keystore + password.
- `session run --new-wallet` menyimpan wallet **tanpa enkripsi**. Tidak dipakai.
- `session run` dan `launch --pay wallet` sama-sama butuh `--miner` dan `--endpoint` miner. Tanpa
  `--endpoint`, CLI memakai `http://127.0.0.1:8645` (mesin miner sendiri). Endpoint miner tidak
  ada on-chain maupun di explorer, dan indexer offer testnet belum dipublikasi (CLI hanya punya
  indexer devnet; `testnet.flopscan.io/api/session-offers` 404). **Untuk agent publik, tahap
  sesi belum bisa jalan.**
- Escrow minimum force-open = kapasitas miner (G/s) × durasi (blok) × tarif. Miner 90.000 G/s
  dengan durasi 1200 blok butuh sekitar 4,5 FLOP, padahal faucet cuma 10 FLOP. Channel yang settled
  di explorer kebanyakan memakai miner kecil (sekitar 50 G/s) dengan escrow 0,005 FLOP. Script
  membatasi escrow maksimal 0,05 FLOP.
- Gateway testnet belum stabil: sempat menampilkan 2 model, beberapa menit kemudian `/health`
  timeout dan daftar model kosong.
- Explorer: 483 miner terdaftar, sekitar 1.679 agent aktif. Finality sempat tertinggal lebih dari
  300 blok, lalu pulih (lag 6).

## Script: `flop/agent_setup.sh`

Tahap terpisah, tidak ada yang berantai otomatis: `check` → `install` → `keygen` → `faucet` →
`balance` → `session`. Tiap tahap mengecek genesis dulu. Wallet ada di
`~/.flop/agent-testnet/` (mode 700) dan log aktivitas di `activity.log`. `install` dan `session`
minta konfirmasi y/N.

## Langkah (jalan di mesin bos sendiri, misalnya VPS bot)

Container sesi Claude ini sementara (bisa hilang), jadi **wallet jangan dibuat di sini**.

1. Pasang CLI (Node 22+), dengan versi dipatok:
   ```bash
   p="$HOME/.local/share/flop-cli/0.10.3"
   npm install --prefix "$p" @flop-labs/cli@0.10.3
   export PATH="$p/node_modules/.bin:$PATH"
   flop --version
   flop --network testnet network status --json   # matches_expected harus true
   ```
2. Buat wallet testnet khusus, dalam bentuk keystore terenkripsi (password di env, bukan di
   chat atau file repo). Wallet ini hanya untuk testnet, jangan dipakai untuk aset lain.
3. Cek faucet sebelum klaim: `/chain` harus menunjukkan genesis `0x918abd58…cfd800`, dan `/limits`
   harus `faucet.status: open`. Lalu:
   ```bash
   flop --network testnet --keystore agent.json --password-env FLOP_PW faucet request
   ```
   Simpan `tx_hash` dan `nonce`. Dana baru boleh dianggap ada setelah transaksinya **final**.
   Kalau jawabannya hilang, ulangi dengan `--nonce <n>` yang sama (tidak akan dibayar dua kali).
   Jangan retry dalam loop.
4. Beli inference dari wallet sendiri (channel langsung ke miner):
   ```bash
   flop --network testnet --keystore agent.json --password-env FLOP_PW session run \
     --miner '<miner-ss58>' --model qwen/qwen3-8b --prompt 'Reply OK.' \
     --max-flop 0.01 --max-tokens 64 --via auto --json
   ```
   - Miner diambil dari `price_sources` di `/v1/models`. Jangan pakai miner milik sendiri.
   - Untuk testnet, cara menemukan endpoint miner belum terdokumentasi. Cek dulu
     `flop --network testnet network status` dan opsi `--endpoint`.
   - Escrow harus menutup minimum open-path dan tarif turn (rumus di
     ask.flop.finance/docs/send-to-specific-miner). Contoh di sana: sekitar 0,0072 FLOP.
   - Bukti sesi settled: `ChannelOpened` final, turn terverifikasi, `Settled.minerPaid`, dan baris
     compute-channel di https://testnet.flopscan.io/ menunjuk miner yang sama. Simpan ID channel.
5. Setelah fase scored aktif: lakukan inference yang **benar-benar dipakai** (misalnya bot ini
   memakai FLOP untuk tugas nyata), rutin, dari satu identitas. Jangan sesi kosong berulang.

## Batas keamanan

- Wallet, klaim faucet, dan setiap `session run` berbayar hanya atas perintah bos.
- Tidak ada seed phrase atau password di chat, di repo, atau di log.
- Cek genesis sebelum menandatangani apa pun (CLI 0.9.0+ sudah menolak genesis yang beda).
- Abaikan link "claim" atau "airdrop" di luar https://flop.finance/official/.
