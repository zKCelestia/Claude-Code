#!/usr/bin/env bash
# FLOP Testnet — setup peran Agent, bertahap dan dengan rem.
#
# Jalankan di mesin bos sendiri (VPS), sebagai user biasa (bukan root). Tiap tahap harus
# dipanggil sendiri. Tidak ada yang otomatis berantai.
#
#   bash flop/agent_setup.sh check      # cek jaringan, faucet, gateway (read-only)
#   bash flop/agent_setup.sh install    # pasang @flop-labs/cli versi terpatok
#   bash flop/agent_setup.sh keygen     # buat keystore sr25519 terenkripsi
#   bash flop/agent_setup.sh faucet     # klaim 10 test FLOP (signed agent claim)
#   bash flop/agent_setup.sh balance    # saldo wallet
#   bash flop/agent_setup.sh session --miner <ss58> --endpoint <https-url> [--max-flop 0.01]
#
# Password keystore diambil dari env FLOP_PW. Kalau kosong, ditanya tanpa ditampilkan.
# Seed phrase tidak pernah ditampilkan: backup-nya adalah file keystore + password.
# Status testnet: unscored. Aktivitas sekarang tidak dihitung untuk airdrop.
set -euo pipefail
umask 077

CLI_VERSION="0.10.3"
GENESIS="0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800"
RPC="https://testnet.flop.network/"
FAUCET="https://faucet.flop.network"
GATEWAY="https://gateway.testnet.flop.network"
MAX_FLOP_CAP="0.05"   # batas keras escrow per sesi; cooperative close membayar semua escrow
DIR="${FLOP_AGENT_DIR:-$HOME/.flop/agent-testnet}"
KEYSTORE="$DIR/agent.json"
LOG="$DIR/activity.log"
CLI_PREFIX="$HOME/.local/share/flop-cli/$CLI_VERSION"
export PATH="$CLI_PREFIX/node_modules/.bin:$PATH"

die() { echo "STOP: $*" >&2; exit 1; }
info() { echo "• $*"; }

need() { command -v "$1" >/dev/null 2>&1 || die "butuh '$1' terpasang"; }

json_get() {  # json_get <python-expr pada d>  (stdin = JSON)
  python3 -I -c "import json,sys; d=json.load(sys.stdin); print($1)"
}

log() {
  mkdir -p "$DIR"; chmod 700 "$DIR"
  printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >>"$LOG"
}

check_genesis() {
  local g
  g=$(curl -fsS -m 20 "$RPC" -H 'content-type: application/json' \
      -d '{"jsonrpc":"2.0","id":1,"method":"chain_getBlockHash","params":[0]}' | json_get 'd["result"]') \
    || die "RPC testnet tidak bisa dibaca"
  [ "$g" = "$GENESIS" ] || die "genesis RPC beda ($g). Mungkin testnet di-reset, jangan tanda tangan apa pun."
  info "genesis RPC cocok"
}

check_faucet_chain() {
  local c
  c=$(curl -fsS -m 20 "$FAUCET/chain") || die "faucet /chain tidak bisa dibaca"
  [ "$(echo "$c" | json_get 'd["network"]')" = "testnet" ] || die "faucet bukan testnet"
  [ "$(echo "$c" | json_get 'd["genesisHash"]')" = "$GENESIS" ] || die "faucet menyebut genesis lain"
  info "faucet /chain cocok"
}

soft() {  # soft <url> <expr>: baca JSON, tanpa menghentikan script kalau gagal
  local body
  body=$(curl -fsS -m 20 "$1" 2>/dev/null) || { echo "tidak terjangkau"; return 0; }
  echo "$body" | json_get "$2" 2>/dev/null || echo "jawaban tidak dikenali"
}

faucet_status() {
  curl -fsS -m 20 "$FAUCET/limits" | json_get 'd["faucet"]["status"] + " | agent " + str(d["faucet"]["agent"]["grantFlop"]) + " FLOP/24j | claimPath " + d["faucet"]["agent"]["claimPath"]'
}

password() {
  if [ -z "${FLOP_PW:-}" ]; then
    read -r -s -p "Password keystore: " FLOP_PW; echo
    [ -n "$FLOP_PW" ] || die "password kosong"
  fi
  export FLOP_PW
}

flop_tn() {  # flop dengan jaringan + keystore testnet
  command -v flop >/dev/null 2>&1 || die "CLI belum terpasang, jalankan: $0 install"
  flop --network testnet --keystore "$KEYSTORE" --password-env FLOP_PW "$@"
}

address() {
  [ -f "$KEYSTORE" ] || die "keystore belum ada, jalankan: $0 keygen"
  python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['address'])" "$KEYSTORE"
}

confirm() {
  local a; read -r -p "$1 [y/N] " a
  [ "$a" = "y" ] || [ "$a" = "Y" ] || die "dibatalkan"
}

cmd_check() {
  need curl; need python3
  check_genesis
  check_faucet_chain
  info "faucet: $(faucet_status)"
  info "gateway: $(soft "$GATEWAY/health" 'd["status"] + ", genesis " + ("cocok" if d["network"]["observed_genesis_hash"]=="'"$GENESIS"'" else "BEDA")')"
  info "model: $(soft "$GATEWAY/v1/models" '", ".join(m["id"] for m in d["data"]) or "(kosong)"')"
  if [ -f "$KEYSTORE" ]; then info "wallet: $(address)"; else info "wallet: belum dibuat"; fi
}

cmd_install() {
  need node; need npm
  local major; major=$(node -p 'process.versions.node.split(".")[0]')
  [ "$major" -ge 22 ] || die "butuh Node.js 22+, terpasang $(node -v)"
  info "integritas paket di registry: $(npm view "@flop-labs/cli@$CLI_VERSION" dist.integrity)"
  confirm "Pasang @flop-labs/cli@$CLI_VERSION ke $CLI_PREFIX?"
  npm install --prefix "$CLI_PREFIX" --no-fund --no-audit "@flop-labs/cli@$CLI_VERSION"
  flop --version
  flop --network testnet network status --json | json_get '"network status matches_expected=" + str(d.get("matches_expected", d))'
  echo "Tambahkan ke ~/.bashrc:  export PATH=\"$CLI_PREFIX/node_modules/.bin:\$PATH\""
}

cmd_keygen() {
  [ ! -e "$KEYSTORE" ] || die "keystore sudah ada di $KEYSTORE (tidak ditimpa)"
  command -v flop >/dev/null 2>&1 || die "CLI belum terpasang, jalankan: $0 install"
  mkdir -p "$DIR"; chmod 700 "$DIR"
  password
  flop keys generate --type sr25519 --name flop-agent-testnet --out "$KEYSTORE" --password-env FLOP_PW --json
  chmod 600 "$KEYSTORE"
  log "keygen address=$(address)"
  echo
  echo "Wallet testnet: $(address)"
  echo "BACKUP: simpan salinan $KEYSTORE dan password-nya di tempat terpisah."
  echo "Tanpa keduanya wallet tidak bisa dipulihkan. Jangan kirim ke chat atau commit ke repo."
}

cmd_faucet() {
  need curl; need python3
  check_genesis
  check_faucet_chain
  local st; st=$(faucet_status); info "faucet: $st"
  case "$st" in open*) ;; *) die "faucet belum 'open' (lihat status di atas). Coba lagi nanti, jangan diulang terus.";; esac
  local nonce="${1:-}"
  if [ -n "$nonce" ]; then
    info "mengulang klaim lama dengan nonce $nonce (tidak akan dibayar dua kali)"
  else
    nonce=$(python3 -I -c 'import time; print(int(time.time()*1000))')
  fi
  password
  log "faucet request address=$(address) nonce=$nonce"
  local out; out=$(flop_tn faucet request --nonce "$nonce" --json) || { echo "$out"; log "faucet gagal nonce=$nonce"; die "klaim ditolak/gagal. Ikuti 'reason' dan 'action' di atas."; }
  echo "$out"
  log "faucet result nonce=$nonce $(echo "$out" | tr -d '\n' | head -c 400)"
  echo "Dana baru boleh dipakai setelah transaksinya final. Cek ulang: $0 faucet-recheck $nonce"
}

cmd_balance() {
  password
  flop_tn balance "$(address)" --json
}

cmd_session() {
  local miner="" endpoint="" max_flop="0.01" model="qwen/qwen3-8b" prompt="Reply OK."
  while [ $# -gt 0 ]; do
    case "$1" in
      --miner) miner="$2"; shift 2;;
      --endpoint) endpoint="$2"; shift 2;;
      --max-flop) max_flop="$2"; shift 2;;
      --model) model="$2"; shift 2;;
      --prompt) prompt="$2"; shift 2;;
      *) die "opsi tidak dikenal: $1";;
    esac
  done
  [ -n "$miner" ] && [ -n "$endpoint" ] || die "butuh --miner <ss58> dan --endpoint <https-url> (endpoint miner testnet belum dipublikasi resmi)"
  case "$endpoint" in https://*) ;; *) die "endpoint harus https://";; esac
  python3 -I -c "import sys; from decimal import Decimal as D; sys.exit(0 if D('0') < D(sys.argv[1]) <= D(sys.argv[2]) else 1)" "$max_flop" "$MAX_FLOP_CAP" \
    || die "--max-flop harus > 0 dan <= $MAX_FLOP_CAP"
  check_genesis
  password
  local me; me=$(address)
  [ "$miner" != "$me" ] || die "miner tidak boleh wallet sendiri"
  echo "Sesi: model=$model miner=$miner"
  echo "      endpoint=$endpoint escrow=$max_flop FLOP (dibayar penuh ke miner kalau settle) + fee transaksi"
  confirm "Lanjut buka channel dan bayar?"
  log "session start miner=$miner model=$model escrow=$max_flop"
  local out rc=0
  out=$(flop_tn session run --miner "$miner" --endpoint "$endpoint" --model "$model" \
        --prompt "$prompt" --max-flop "$max_flop" --max-tokens 64 --via auto --json) || rc=$?
  echo "$out"
  log "session rc=$rc $(echo "$out" | tr -d '\n' | head -c 600)"
  [ "$rc" -eq 0 ] || die "sesi gagal. Simpan channel ID di atas, jangan diulang buta."
  echo "Verifikasi di https://testnet.flopscan.io/ : channel harus berstatus settled/PAID ke miner yang sama."
}

case "${1:-}" in
  check) cmd_check;;
  install) cmd_install;;
  keygen) cmd_keygen;;
  faucet) cmd_faucet;;
  faucet-recheck) [ -n "${2:-}" ] || die "butuh nonce"; cmd_faucet "$2";;
  balance) cmd_balance;;
  session) shift; cmd_session "$@";;
  *) sed -n '2,17p' "$0"; exit 2;;
esac
