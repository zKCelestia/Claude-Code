"""Kirim laporan ke Telegram lewat Bot API biasa (gratis, tanpa AI).

Butuh TELEGRAM_BOT_TOKEN (dari @BotFather) dan ALLOWED_USER_IDS (ID Telegram, dipisah koma)
di .env. Penerima harus sudah pernah kirim /start ke bot itu.
"""

import os

import requests


def targets() -> tuple[str | None, list[str]]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None
    ids = [x for x in os.environ.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x]
    return token, ids


def send(text: str, http=requests) -> list[str]:
    """Kirim ke semua ID. Mengembalikan daftar error (kosong = semua terkirim)."""
    token, ids = targets()
    if not token or not ids:
        return ["TELEGRAM_BOT_TOKEN atau ALLOWED_USER_IDS belum diisi di .env"]
    errors = []
    for chat_id in ids:
        try:
            r = http.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True},
                timeout=30,
            )
            if not r.ok:
                desc = r.json().get("description", r.status_code) if r.content else r.status_code
                errors.append(f"{chat_id}: {desc}")
        except requests.RequestException as e:
            errors.append(f"{chat_id}: {type(e).__name__}")
    return errors
