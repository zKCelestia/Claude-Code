# Asisten AI di Telegram (Claude Managed Agents)

Bot Telegram yang menjawab chat dengan AI agent dari Claude. Agent punya workspace
sendiri (bash, file, Python) untuk menghitung dan mengolah data, dan ingat isi percakapan
per chat.

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
