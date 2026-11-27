"""Pemantau FLOP Network (flop.finance), read-only.

Yang dicek tiap jalan:
- RPC testnet resmi: genesis hash harus sama dengan yang diumumkan, blok final terbaru,
  dan specVersion runtime. specVersion naik = runtime upgrade. Voucher earning (fase
  scored) baru mulai di blok final sebuah upgrade yang diumumkan, jadi upgrade itu sinyal
  untuk cek pengumuman di @flop_labs / halaman official.
- Endpoint faucet testnet (/chain dan /limits): identitas jaringan dan status faucet.
- Halaman resmi (official, testnet, airdrop, docs testnet): kalimat baru yang memuat kata
  kunci (voucher, scored, snapshot, claim, ...) dilaporkan.

Tidak membuat wallet, tidak klaim faucet, tidak menandatangani apa pun, tidak mengklik link.
State disimpan di flop/state.json (lokal, tidak di-commit).

Pemakaian:
    python -m flop.watch            # laporan + simpan state
    python -m flop.watch --json     # keluaran JSON
Exit code 0 = tidak ada yang berubah, 1 = ada perubahan penting, 2 = verifikasi gagal.
"""

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

DIR = Path(__file__).resolve().parent
STATE = DIR / "state.json"
UA = {"User-Agent": "Mozilla/5.0 (flop-watch)"}

RPC = "https://testnet.flop.network/"
# Diumumkan di flop.finance/official dan docs.flop.network/networks/testnet (dibaca 2026-11-27).
GENESIS = "0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800"
FINALITY_LAG_ALERT = 120  # blok (~2 menit di ~1 dtk/blok)
FAUCET_CHAIN = "https://faucet.flop.network/chain"
FAUCET_LIMITS = "https://faucet.flop.network/limits"

PAGES = {
    "official": "https://flop.finance/official/",
    "testnet": "https://flop.finance/testnet/",
    "airdrop": "https://flop.finance/airdrop/",
    "docs-testnet": "https://docs.flop.network/networks/testnet",
}
KEYWORDS = re.compile(
    r"voucher|scored|snapshot|claim|eligib|registration|enrol|seat|upgrade|"
    r"contract address|mainnet|tge|reset|agent|miner|validator",
    re.I,
)


def rpc(method: str, params: list | None = None):
    r = requests.post(
        RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []},
        headers=UA,
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(f"{method}: {body['error']}")
    return body["result"]


def chain_status() -> dict:
    genesis = rpc("chain_getBlockHash", [0])
    head = rpc("chain_getFinalizedHead")
    header = rpc("chain_getHeader", [head])
    runtime = rpc("state_getRuntimeVersion")
    best = int(rpc("chain_getHeader")["number"], 16)
    finalized = int(header["number"], 16)
    return {
        "chain": rpc("system_chain"),
        "genesis": genesis,
        "genesis_ok": genesis == GENESIS,
        "finalized": finalized,
        "best": best,
        "finality_lag": best - finalized,
        "spec_version": runtime["specVersion"],
        "spec_name": runtime["specName"],
        "node_version": rpc("system_version"),
    }


def faucet_status() -> dict:
    chain = requests.get(FAUCET_CHAIN, headers=UA, timeout=30).json()
    limits = requests.get(FAUCET_LIMITS, headers=UA, timeout=30).json()
    f = limits.get("faucet", {})
    return {
        "genesis_ok": chain.get("genesisHash") == GENESIS,
        "status": f.get("status"),
        "agent_grant": f.get("agent", {}).get("grantFlop"),
        "miner_sponsor": limits.get("sponsor", {}).get("miner", {}).get("status"),
        "validator_sponsor": limits.get("sponsor", {}).get("validator", {}).get("status"),
        "as_of": limits.get("asOf"),
    }


def page_sentences(url: str) -> list[str]:
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", r.text)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(re.sub(r"\s+", " ", t))
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if KEYWORDS.search(p) and 20 <= len(p.strip()) <= 600]


def digest(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def check(state: dict) -> tuple[dict, list[str], bool]:
    """Kembalikan (state baru, daftar alert, verifikasi_ok)."""
    alerts: list[str] = []
    ok = True
    new = dict(state)

    try:
        c = chain_status()
        if not c["genesis_ok"]:
            ok = False
            alerts.append(f"GENESIS BEDA: RPC memberi {c['genesis']}. Jangan pakai sampai jelas (mungkin reset).")
        old_spec = state.get("chain", {}).get("spec_version")
        if old_spec is not None and c["spec_version"] != old_spec:
            alerts.append(
                f"Runtime upgrade: specVersion {old_spec} -> {c['spec_version']} di sekitar blok "
                f"{c['finalized']}. Cek @flop_labs dan /official/ soal mulainya voucher earning."
            )
        if c["finality_lag"] > FINALITY_LAG_ALERT:
            alerts.append(
                f"Finality tertinggal {c['finality_lag']} blok (best {c['best']}, final {c['finalized']}). "
                "Jangan anggap transaksi beres sebelum final."
            )
        old_fin = state.get("chain", {}).get("finalized")
        if old_fin is not None and c["finalized"] < old_fin:
            alerts.append(f"Blok final mundur ({old_fin} -> {c['finalized']}): kemungkinan testnet di-reset.")
        new["chain"] = c
    except Exception as e:  # noqa: BLE001 - laporan saja
        ok = False
        alerts.append(f"RPC testnet gagal: {e}")

    try:
        f = faucet_status()
        if not f["genesis_ok"]:
            ok = False
            alerts.append("Faucet /chain menyebut genesis lain. Jangan klaim dulu.")
        old = state.get("faucet", {})
        for k in ("miner_sponsor", "validator_sponsor"):
            if old.get(k) and f[k] != old.get(k):
                alerts.append(f"Status sponsor {k.split('_')[0]} berubah: {old.get(k)} -> {f[k]}")
        new["faucet"] = f
    except Exception as e:  # noqa: BLE001
        alerts.append(f"Faucet tidak bisa dibaca: {e}")

    pages = dict(state.get("pages", {}))
    for name, url in PAGES.items():
        try:
            sents = page_sentences(url)
        except Exception as e:  # noqa: BLE001
            alerts.append(f"Halaman {name} gagal dibaca: {e}")
            continue
        hashes = {digest(s) for s in sents}
        known = set(pages.get(name, []))
        if known:
            fresh = [s for s in sents if digest(s) not in known]
            for s in fresh[:8]:
                alerts.append(f"[{name}] kalimat baru: {s}")
            if len(fresh) > 8:
                alerts.append(f"[{name}] +{len(fresh) - 8} kalimat baru lain: {url}")
        pages[name] = sorted(hashes)
    new["pages"] = pages
    new["checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return new, alerts, ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()

    first_run = not STATE.exists()
    state, alerts, ok = check(load_state())
    if not a.no_save:
        STATE.write_text(json.dumps(state, indent=1))

    if a.json:
        print(json.dumps({"ok": ok, "alerts": alerts, "chain": state.get("chain"), "faucet": state.get("faucet")}, indent=1))
    else:
        c, f = state.get("chain", {}), state.get("faucet", {})
        print(f"FLOP Testnet — cek {state['checked_at']}")
        if c:
            print(f"  genesis {'cocok' if c['genesis_ok'] else 'TIDAK COCOK'} | final {c['finalized']:,} / "
                  f"best {c['best']:,} (lag {c['finality_lag']})\n"
                  f"  runtime {c['spec_name']} v{c['spec_version']} | node {c['node_version']}")
        if f:
            print(f"  faucet: {f['status']} (agent {f['agent_grant']} FLOP/24 jam) | sponsor miner: "
                  f"{f['miner_sponsor']} | sponsor validator: {f['validator_sponsor']}")
        if first_run:
            print("  Jalan pertama: kondisi awal dicatat, perubahan dilaporkan mulai jalan berikutnya.")
        for line in alerts:
            print("  ! " + line)
        if not alerts and not first_run:
            print("  Tidak ada perubahan.")
    if not ok:
        return 2
    return 1 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
