# Asisten AI di Telegram (Claude Managed Agents)

Bot Telegram yang menjawab chat dengan AI agent dari Claude. Agent punya workspace
sendiri (bash, file, Python) untuk menghitung dan mengolah data, dan ingat isi percakapan
per chat.

## Skill

Agent dilengkapi skill bawaan Anthropic:

| Skill | Contoh permintaan |
|---|---|
| `xlsx` (Excel) | "Buatkan tabel cicilan 12 bulan dalam Excel", kirim file .xlsx lalu "hitung totalnya" |
| `docx` (Word) | "Buatkan surat penawaran dalam Word" |
| `pptx` (PowerPoint) | "Buat 5 slide presentasi tentang produk saya" |
| `pdf` | Kirim PDF lalu "ringkas isinya", atau "jadikan ini PDF" |

Kamu bisa mengirim file atau foto ke bot (maksimal 20 MB). File yang dibuat agent
langsung dikirim balik ke chat sebagai dokumen.

## Pustaka skill (asa-skills-pack)

Repo ini memuat **428 skill** di `.claude/skills/` (lihat `.claude/skills/CATALOG.md`).
Claude Code memuatnya otomatis berdasarkan deskripsi tiap skill, jadi tidak perlu
diaktifkan manual. Isinya antara lain security/bug-bounty, crypto/trading, otomasi, dan
pembuatan konten.

> Catatan: grup `built-in-skills` dari pack asli **tidak** dipasang karena formatnya untuk
> platform lain (tidak punya frontmatter). Skill dengan deskripsi > 1024 karakter juga
> dilewati karena ditolak format standar.

### Memakai skill ini di bot Telegram

Agent bot tidak otomatis mengenal isi `.claude/skills/`. Untuk memasangnya, unggah ke
akun Anthropic-mu lalu daftarkan ke agent:

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # atau `ant auth login`
python upload_skills_to_bot.py          # unggah semua (ratusan — makan kredit & waktu)
python setup_agent.py                   # pasang skill yang terunggah ke agent
```

- `upload_skills_to_bot.py` idempoten: skill yang sudah terunggah dilewati
  (dicatat di `uploaded_skills.json`), jadi aman diulang bila terputus.
- Ingin sebagian saja? `python upload_skills_to_bot.py nama-skill-1 nama-skill-2`.
- Aset berat (video/font/gambar) dilewati saat unggah agar paket skill kecil.
- Hapus skill yang tak terpakai lewat Console (platform.claude.com) bila perlu.

## Burner wallet (garapan otomatis)

Bot bisa memakai **burner wallet** EVM + Solana bersaldo kecil untuk mint dan tugas
airdrop secara otomatis, termasuk berkala tanpa disuruh (autopilot). Agent tidak pernah
memegang private key. Agent hanya mengirim permintaan lewat tool `burner_*`, lalu bot
menandatanganinya di mesinmu **setelah lolos guard**.

**Guard yang selalu aktif** (`burner/policy.py`):

- Batas pengeluaran per transaksi dan per hari (UTC), per chain. Gas ikut dihitung.
- Tujuan harus ada di daftar izin: `allowed_contracts` (EVM), `allowed_programs` dan `allowed_recipients` (Solana).
- Fungsi yang biasa dipakai drainer **selalu diblokir**: `approve`, `setApprovalForAll`, `permit`,
  transfer token/NFT, `multicall`/`aggregate`, serta instruksi SPL Token `Transfer`/`Approve`/`SetAuthority`.
- Tidak ada tool untuk tanda tangan pesan (EIP-712/permit), jadi tidak bisa dipancing tanda tangan "gasless".
- Setiap transaksi disimulasikan dulu. Yang akan revert atau ternyata menguras SOL lebih dari budget ditolak.
- Batas `max_gas_gwei`, kill switch `/stop`, dan semua transaksi tercatat di `burner_ledger.json`.
- Burner **nonaktif kalau `ALLOWED_USER_IDS` kosong**, supaya orang lain tidak bisa memakai saldomu lewat bot.

### Menyiapkan

```bash
python -m burner.create_wallets                 # buat wallet, key ke .env.burner (izin 600)
cp burner/policy.example.json burner_policy.json
# edit burner_policy.json: RPC, batas, kontrak/program yang diizinkan, daftar tugas autopilot
python setup_agent.py                           # daftarkan tool burner ke agent
python bot.py
```

Lalu isi alamat yang dicetak dengan saldo **seperlunya saja**. Di Telegram:

| Perintah | Fungsi |
|---|---|
| `/wallet` | Alamat, saldo, sisa budget hari ini |
| `/stop` | Pause semua transaksi burner |
| `/resume` | Aktifkan lagi |

Contoh perintah: "mint NFT gratis di kontrak 0x... di Base" (kontraknya harus sudah ada di
`allowed_contracts`). Setiap transaksi dan penolakan dilaporkan ke chat.

### Autopilot (jalan sendiri)

Di `burner_policy.json`, set `"autopilot": {"enabled": true, "interval_hours": 6, "prompt": "..."}`
dan tulis daftar garapanmu di `prompt`. Bot menjalankannya berkala dan mengirim laporan ke
setiap ID di `ALLOWED_USER_IDS`. Autopilot berhenti saat `/stop`.

### Catatan penting

- Pakai wallet ini **hanya** untuk garapan. Jangan pindahkan aset berharga ke sana.
- Tidak ada fitur multi-wallet/sybil. Itu melanggar aturan hampir semua airdrop dan biasanya berujung diskualifikasi.
- Akses web agent defaultnya mati. Agar agent bisa membuka situs mint/garapan, nyalakan web
  dan daftarkan host-nya (lihat "Menyalakan pencarian web").
- Test guard: `pip install "web3[tester]" pytest && pytest tests/`

## Cara kerja

- **`setup_agent.py`** dijalankan sekali. Script ini membuat *Environment* dan *Agent* di
  Claude Managed Agents, lalu menyimpan ID-nya ke `agent_config.json`.
- **`bot.py`** menerima pesan Telegram (long polling). Setiap chat mendapat satu
  *session* agent (disimpan di `sessions.json`), lalu balasan agent dikirim kembali ke Telegram.

Loop agent dan container tempat tools berjalan di-hosting oleh Anthropic. Kamu cukup
menjalankan `bot.py` di komputer atau server mana pun.

## Persiapan

1. **Token bot Telegram**: chat [@BotFather](https://t.me/BotFather), kirim `/newbot`, salin tokennya.
2. **Kunci API Anthropic**: buat di <https://platform.claude.com>.
3. Instal:

   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env               # lalu isi ANTHROPIC_API_KEY dan TELEGRAM_BOT_TOKEN
   ```

4. Buat agent (sekali saja):

   ```bash
   python setup_agent.py
   ```

5. Jalankan bot:

   ```bash
   python bot.py
   ```

Buka bot kamu di Telegram dan mulai chat. Ketik `/reset` untuk memulai percakapan baru.

## Pengaturan

| Yang ingin diubah | Caranya |
|---|---|
| Kepribadian / instruksi agent | Ubah `SYSTEM_PROMPT` di `setup_agent.py`, lalu jalankan `python setup_agent.py` lagi (agent diperbarui ke versi baru, tidak dibuat ulang) |
| Model | Ubah `MODEL` di `setup_agent.py` (default `claude-opus-5-5`) |
| Siapa yang boleh memakai bot | Isi `ALLOWED_USER_IDS` di `.env` dengan ID Telegram (cek lewat @userinfobot), dipisah koma |
| Akses internet (cari web) | Lihat di bawah |
| Skill | Ubah daftar `SKILLS` di `setup_agent.py`, lalu jalankan `python setup_agent.py` lagi |

### Menambah skill buatan sendiri

Skill adalah folder berisi `SKILL.md` (instruksi) beserta script atau file pendukung.
Unggah lewat Skills API atau Console (platform.claude.com), lalu tambahkan ID-nya ke
`SKILLS`:

```python
{"type": "custom", "skill_id": "skill_xxx", "version": "latest"},
```

### Menyalakan pencarian web

Secara default `web_search` dan `web_fetch` dimatikan. Untuk menyalakan:

1. Di `setup_agent.py`, ubah `"enabled": False` menjadi `True` pada `web_search` dan `web_fetch`.
2. Jaringan environment bertipe `limited`, sehingga tools web hanya bisa menjangkau host
   yang terdaftar. Tambahkan `"allowed_hosts": ["contoh.com", ...]` di bagian `networking`,
   atau ganti ke `{"type": "unrestricted"}`. Hati-hati: `unrestricted` membuka akses internet
   penuh untuk seluruh container, bukan hanya tools web.
3. Karena environment sudah dibuat, hapus `environment_id` dari `agent_config.json` lalu
   jalankan `python setup_agent.py` lagi.

## Catatan

- Managed Agents masih **beta**. Biaya = token model + waktu berjalan session.
  Riwayat session disimpan di akun Anthropic kamu sampai dihapus.
- Aksi yang dinilai berisiko oleh agent otomatis **ditolak** karena tidak ada yang
  menyetujuinya dari Telegram.
- Transkrip setiap session bisa dilihat di Console: platform.claude.com, menu Sessions.
