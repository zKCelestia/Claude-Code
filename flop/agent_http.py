"""FLOP Testnet agent lewat HTTP saja (tanpa WebSocket), untuk lingkungan yang proxy-nya
menolak WebSocket. Hanya dua aksi: baca status, dan klaim faucet agent (10 test FLOP / 24 jam).

    python flop/agent_http.py status
    python flop/agent_http.py claim      # satu percobaan, tidak pernah retry dalam loop

Butuh `pip install substrate-interface`. Keystore: $FLOP_KEYSTORE (default
~/.flop/agent-testnet/agent.json), password: $FLOP_PW_FILE (default
~/.flop/agent-testnet/password). Keduanya rahasia dan tidak boleh masuk repo.
Catatan klaim: ~/.flop/agent-testnet/claims.json.

Aturan yang dipegang:
- Genesis RPC dan faucet /chain harus sama dengan genesis yang diumumkan, kalau tidak berhenti.
- Klaim hanya kalau /limits bilang `open` dan claimPath sesuai.
- Nonce dicatat sebelum dikirim. Klaim yang belum final dicek ulang dengan nonce yang sama
  (faucet tidak membayar dua kali), bukan nonce baru.
- Grant berikutnya butuh grant sebelumnya sudah dipakai (rolloverRequiresSpend). Selama belum
  ada spend, klaim baru tidak dikirim.
- Dana dianggap masuk hanya kalau terlihat di blok final.

Exit code: 0 ok/tidak ada aksi, 1 klaim dikirim / ada perubahan, 2 berhenti karena pemeriksaan gagal.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

GENESIS = "0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800"
RPC = "https://testnet.flop.network/"
FAUCET = "https://faucet.flop.network"
OFFERS = "https://testnet.flopscan.io/api/session-offers"
HOME = Path(os.environ.get("FLOP_AGENT_DIR", Path.home() / ".flop" / "agent-testnet"))
KEYSTORE = Path(os.environ.get("FLOP_KEYSTORE", HOME / "agent.json"))
PW_FILE = Path(os.environ.get("FLOP_PW_FILE", HOME / "password"))
CLAIMS = HOME / "claims.json"
UA = {"User-Agent": "flop-agent-http"}


class Stop(Exception):
    pass


def rpc(method, params=None):
    r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []},
                      headers=UA, timeout=30)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise Stop(f"RPC {method}: {body['error']}")
    return body["result"]


def check_network():
    g = rpc("chain_getBlockHash", [0])
    if g != GENESIS:
        raise Stop(f"genesis RPC beda ({g}); kemungkinan reset, jangan tanda tangan")
    c = requests.get(f"{FAUCET}/chain", headers=UA, timeout=30).json()
    if c.get("network") != "testnet" or c.get("genesisHash") != GENESIS:
        raise Stop("faucet /chain tidak cocok dengan genesis testnet")


def limits():
    return requests.get(f"{FAUCET}/limits", headers=UA, timeout=30).json()


def address():
    if not KEYSTORE.exists():
        raise Stop(f"keystore tidak ada di {KEYSTORE} (upload ulang flop-agent-testnet.json)")
    return json.loads(KEYSTORE.read_text())["address"]


def keypair():
    from substrateinterface import Keypair
    if not PW_FILE.exists():
        raise Stop(f"file password tidak ada di {PW_FILE}")
    kp = Keypair.create_from_encrypted_json(json.loads(KEYSTORE.read_text()), PW_FILE.read_text().strip(),
                                           ss58_format=42)
    if kp.ss58_address != address():
        raise Stop("keystore terbuka ke alamat lain")
    return kp


def finalized_balance(addr):
    from substrateinterface import SubstrateInterface
    s = SubstrateInterface(url=RPC, ss58_format=42)
    head = s.get_chain_finalised_head()
    acct = s.query("System", "Account", [addr], block_hash=head).value
    number = s.get_block_number(head)
    return acct["data"]["free"] / 10**18, acct["nonce"], number


def load_claims():
    try:
        return json.loads(CLAIMS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_claims(claims):
    HOME.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = CLAIMS.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(claims, f, indent=1)
    tmp.replace(CLAIMS)


def offers_published():
    try:
        r = requests.get(OFFERS, headers=UA, timeout=20)
        return r.status_code == 200
    except requests.RequestException:
        return False


def status():
    check_network()
    addr = address()
    free, nonce, block = finalized_balance(addr)
    lim = limits()
    f = lim.get("faucet", {})
    claims = load_claims()
    print(f"wallet {addr}")
    print(f"  saldo final {free:.6f} FLOP | nonce akun {nonce} | blok final {block}")
    print(f"  faucet {f.get('status')} | sisa kuota harian {f.get('dailyCap', {}).get('remainingFlop')} FLOP "
          f"| asOf {lim.get('asOf')}")
    print(f"  indexer offer testnet {'ADA' if offers_published() else 'belum ada'}")
    if claims:
        last = claims[-1]
        print(f"  klaim terakhir nonce {last['nonce']} status {last.get('state')} @ {last.get('sent_at')}")
    return 0


def claim():
    check_network()
    addr = address()
    claims = load_claims()
    free, acct_nonce, block = finalized_balance(addr)
    last = claims[-1] if claims else None

    # Klaim lama belum final: cek ulang dengan nonce yang sama, bukan bikin baru.
    if last and last.get("state") not in ("final", "refused"):
        if free > 0:
            last["state"] = "final"
            last["final_block"] = block
            save_claims(claims)
            print(f"klaim nonce {last['nonce']} sudah final: saldo {free:.6f} FLOP di blok {block}")
            return 1
        nonce = last["nonce"]
        print(f"klaim nonce {nonce} belum final, dicek ulang dengan nonce yang sama")
    else:
        if last and last.get("state") == "final" and acct_nonce == 0:
            print(f"grant sebelumnya belum dipakai (nonce akun 0, saldo {free:.6f}); faucet butuh spend dulu. Tidak klaim.")
            return 0
        f = limits().get("faucet", {})
        if f.get("status") != "open":
            print(f"faucet {f.get('status')}, belum klaim")
            return 0
        if f.get("agent", {}).get("claimPath") != "/v1/testnet/agent-claims":
            raise Stop("claimPath faucet berubah; cek docs dulu")
        nonce = str(int(time.time() * 1000))
        claims.append({"nonce": nonce, "address": addr, "state": "prepared",
                       "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        save_claims(claims)
        last = claims[-1]

    kp = keypair()
    msg = f"flop-faucet-agent/v1|{GENESIS}|{addr}|{nonce}".encode()
    sig = "0x" + kp.sign(msg).hex()
    try:
        r = requests.post(f"{FAUCET}/v1/testnet/agent-claims", headers=UA, timeout=60,
                          json={"address": addr, "nonce": nonce, "signature": sig})
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"text": r.text[:500]}
    except requests.RequestException as e:
        last["state"] = "unknown"
        save_claims(claims)
        print(f"jawaban faucet hilang ({e}); nanti dicek ulang dengan nonce {nonce}")
        return 1
    last["http"] = r.status_code
    last["response"] = body
    if r.ok:
        last["state"] = "sent"
        print(f"klaim diterima HTTP {r.status_code}: {json.dumps(body)[:400]}")
    else:
        action = body.get("action")
        last["state"] = "retry_later" if action == "retry_later" else "refused"
        print(f"klaim ditolak HTTP {r.status_code}: reason={body.get('reason')} action={action} "
              f"error={body.get('error')}")
    save_claims(claims)
    return 1


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "status":
            return status()
        if cmd == "claim":
            return claim()
        print(__doc__)
        return 2
    except Stop as e:
        print(f"STOP: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
