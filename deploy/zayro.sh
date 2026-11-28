#!/usr/bin/env bash
# Garap zayro.trade otomatis di VPS, GRATIS: tanpa bot AI, tanpa API Anthropic.
# Cron jalan tiap jam, laporan dikirim lewat bot Telegram biasa (@BotFather).
#
#   bash deploy/zayro.sh install     # 1x: python venv, .env, cron
#   nano .env                        # isi TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS (opsional ZAYRO_NAME, ZAYRO_REF)
#   bash deploy/zayro.sh test        # tes kirim pesan ke Telegram
#   bash deploy/zayro.sh run         # garap sekarang (wallet dibuat otomatis kalau belum ada)
#
#   bash deploy/zayro.sh bug "apa yang rusak + cara mengulanginya" [https://link-screenshot]
#   bash deploy/zayro.sh mission follow                # misi X: follow | post|quote|reply URL
#   bash deploy/zayro.sh spin                          # putar roulette sekali (bayar 500 poin)
#   bash deploy/zayro.sh claim ID ALAMAT_BASE|EMAIL LINK_REPLY_X
#   bash deploy/zayro.sh status|log|update|uninstall
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$APP_DIR/.venv/bin/python"
MARK="# zayro-auto"
CRON_LINE="17 * * * * cd '$APP_DIR' && flock -n /tmp/zayro-\$USER.lock '$PY' -m zayro daily --notify >> '$APP_DIR/zayro.log' 2>&1 $MARK"
CMD="${1:-help}"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
need_py() { [ -x "$PY" ] || die "Belum dipasang. Jalankan dulu: bash deploy/zayro.sh install"; }

env_has() { grep -qE "^$1=" "$APP_DIR/.env" 2>/dev/null; }

do_install() {
  local SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO="sudo"

  if ! python3 -c "import ensurepip" >/dev/null 2>&1 || ! command -v flock >/dev/null || ! command -v crontab >/dev/null; then
    say "Paket sistem (python3-venv, cron, util-linux)"
    $SUDO apt-get update -y >/dev/null
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip cron util-linux >/dev/null
  fi

  say "Python venv & dependensi (web3, requests, python-dotenv)"
  [ -x "$PY" ] || python3 -m venv "$APP_DIR/.venv"
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q "web3>=8.0" "requests>=2.31" "python-dotenv>=1.0"

  say "File .env (izin 600)"
  ( umask 077; touch "$APP_DIR/.env" )
  chmod 600 "$APP_DIR/.env"
  for k in TELEGRAM_BOT_TOKEN ALLOWED_USER_IDS ZAYRO_NAME ZAYRO_REF; do
    env_has "$k" || echo "$k=" >>"$APP_DIR/.env"
  done

  say "Cron tiap jam (menit ke-17)"
  ( crontab -l 2>/dev/null | grep -vF "$MARK" || true; echo "$CRON_LINE" ) | crontab -
  $SUDO systemctl enable --now cron >/dev/null 2>&1 || true

  say "Terpasang. Langkah berikutnya:"
  cat <<EOF
  1. nano $APP_DIR/.env   → isi TELEGRAM_BOT_TOKEN dan ALLOWED_USER_IDS
  2. Kirim /start ke bot-mu di Telegram (sekali, supaya bot boleh kirim pesan)
  3. bash deploy/zayro.sh test
  4. bash deploy/zayro.sh run
EOF
}

case "$CMD" in
  install) do_install ;;
  test) need_py; cd "$APP_DIR" && "$PY" -m zayro test-notify ;;
  run) need_py; cd "$APP_DIR" && "$PY" -m zayro daily --notify ;;
  bug|spin|claim|mission) need_py; shift; cd "$APP_DIR" && "$PY" -m zayro "$CMD" "$@" ;;
  status) need_py; cd "$APP_DIR" && "$PY" -m zayro status; echo; crontab -l 2>/dev/null | grep -F "$MARK" >/dev/null && echo "Cron: aktif (tiap jam, menit ke-17)" || echo "Cron: TIDAK aktif" ;;
  log) tail -n 50 "$APP_DIR/zayro.log" 2>/dev/null || echo "Belum ada log." ;;
  update) git -C "$APP_DIR" pull --ff-only && need_py && "$PY" -m pip install -q "web3>=8.0" "requests>=2.31" "python-dotenv>=1.0" && say "Diperbarui." ;;
  uninstall) ( crontab -l 2>/dev/null | grep -vF "$MARK" || true ) | crontab -; say "Cron dihapus. Wallet (.env.zayro) TIDAK dihapus." ;;
  *) sed -n '2,14p' "$0" ;;
esac
