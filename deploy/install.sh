#!/usr/bin/env bash
# Pasang & kelola bot Liz di VPS (Ubuntu/Debian, systemd).
#
#   sudo bash deploy/install.sh            # 1x: paket, venv, .env, service (belum dijalankan)
#   nano .env                              # isi ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
#   sudo bash deploy/install.sh start      # buat agent (sekali) lalu nyalakan bot
#
#   sudo bash deploy/install.sh status|logs|restart|stop|update
#
# Bot berjalan sebagai pemilik folder repo ini (bukan root, kalau repo-nya milik user biasa),
# nyala otomatis saat VPS boot, dan restart sendiri kalau crash / dimatikan watchdog.
set -euo pipefail

SERVICE=lizbot
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="$(stat -c %U "$APP_DIR")"
UNIT="/etc/systemd/system/${SERVICE}.service"
VENV="$APP_DIR/.venv"
CMD="${1:-install}"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
as_app_user() { if [ "$RUN_USER" = "root" ]; then bash -c "$*"; else sudo -u "$RUN_USER" -H bash -c "$*"; fi; }

[ "$(id -u)" -eq 0 ] || die "Jalankan dengan sudo: sudo bash deploy/install.sh $CMD"
command -v systemctl >/dev/null || die "systemd tidak ditemukan. Skrip ini untuk Ubuntu/Debian dengan systemd."

env_value() { grep -E "^$1=" "$APP_DIR/.env" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" ; }

check_env() {
  [ -f "$APP_DIR/.env" ] || die ".env belum ada. Jalankan: sudo bash deploy/install.sh"
  local missing=()
  for k in ANTHROPIC_API_KEY TELEGRAM_BOT_TOKEN ALLOWED_USER_IDS; do
    [ -n "$(env_value "$k")" ] || missing+=("$k")
  done
  [ ${#missing[@]} -eq 0 ] || die "Isi dulu di $APP_DIR/.env: ${missing[*]}"
}

install() {
  say "Paket sistem (python3, venv, git)"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y >/dev/null
  apt-get install -y python3 python3-venv python3-pip git >/dev/null

  say "Virtualenv & dependensi Python (sebagai $RUN_USER)"
  as_app_user "cd '$APP_DIR' && python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt"

  if [ ! -f "$APP_DIR/.env" ]; then
    say "Membuat .env dari .env.example (izin 600)"
    install -m 600 -o "$RUN_USER" "$APP_DIR/.env.example" "$APP_DIR/.env"
  else
    chmod 600 "$APP_DIR/.env"
  fi

  say "Service systemd: $UNIT"
  cat >"$UNIT" <<EOF
[Unit]
Description=Liz - bot Telegram (Claude Managed Agents)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV/bin/python $APP_DIR/bot.py
Restart=always
RestartSec=10
# Pengamanan dasar
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable "$SERVICE" >/dev/null

  say "Selesai dipasang. Langkah berikutnya:"
  cat <<EOF
  1. Edit $APP_DIR/.env dan isi minimal:
       ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
     (opsional: GROUP_CHAT_IDS, X_BEARER_TOKEN)
  2. sudo bash deploy/install.sh start
EOF
}

start() {
  check_env
  if [ ! -f "$APP_DIR/agent_config.json" ]; then
    say "Membuat agent Claude (sekali saja)"
    as_app_user "cd '$APP_DIR' && .venv/bin/python setup_agent.py"
  fi
  if [ ! -f "$APP_DIR/monitor/watchlist.json" ]; then
    say "Membuat monitor/watchlist.json (kosong, isi lewat /pantau di Telegram)"
    as_app_user "cd '$APP_DIR' && .venv/bin/python -c \"import json; d=json.load(open('monitor/watchlist.example.json')); d['telegram']=[]; d['x']=[]; json.dump(d, open('monitor/watchlist.json','w'), indent=2)\""
  fi
  say "Menyalakan $SERVICE"
  systemctl restart "$SERVICE"
  sleep 5
  if systemctl is-active --quiet "$SERVICE"; then
    say "Bot jalan ✅  Coba chat bot-mu di Telegram. Log: sudo bash deploy/install.sh logs"
  else
    journalctl -u "$SERVICE" -n 40 --no-pager
    die "Bot gagal jalan. Lihat log di atas."
  fi
}

update() {
  say "Ambil kode terbaru"
  as_app_user "cd '$APP_DIR' && git pull --ff-only"
  as_app_user "cd '$APP_DIR' && .venv/bin/pip install -q -r requirements.txt"
  if [ -f "$APP_DIR/agent_config.json" ]; then
    say "Perbarui agent (instruksi/tools/skill terbaru)"
    as_app_user "cd '$APP_DIR' && .venv/bin/python setup_agent.py"
  fi
  systemctl restart "$SERVICE"
  say "Diperbarui & di-restart."
}

case "$CMD" in
  install) install ;;
  start) start ;;
  update) update ;;
  restart) systemctl restart "$SERVICE"; systemctl --no-pager status "$SERVICE" | head -5 ;;
  stop) systemctl stop "$SERVICE"; say "Bot dimatikan." ;;
  status) systemctl --no-pager status "$SERVICE" | head -15 ;;
  logs) journalctl -u "$SERVICE" -n 100 -f ;;
  *) die "Perintah tidak dikenal: $CMD (install|start|status|logs|restart|stop|update)" ;;
esac
