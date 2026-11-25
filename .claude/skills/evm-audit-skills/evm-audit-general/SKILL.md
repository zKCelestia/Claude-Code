---
name: evm-audit-general
description: General Solidity/EVM security checklist — non-obvious footguns that apply to every smart contract. Covers external calls, force-feeding, pause mechanisms, read-only reentrancy, merkle trees, code asymmetry, multicall hazards, and general EVM quirks. Load this for EVERY audit.
---

# EVM Audit — General Solidity/EVM Footguns

Load this for **every** EVM smart contract audit. These items are non-obvious issues that apply universally.

## Reference Files
- `references/checklist.md` — Full dense checklist

## SUPER MAXIMUS enrichment — Wave 2 — Wycheproof + zeroize + ProVerif (ToB)

Sumber: trailofbits/skills @ 149d7b21 (CC BY-SA 4.0 — atribusi + ShareAlike wajib; materi turunan di bawah ini dilisensikan CC BY-SA 4.0).
- **Wycheproof** (registry: `wycheproof`): validasi implementasi kriptografi terhadap
  test vector Project Wycheproof (AES, RSA, ECDSA, ECDH, dst) yang mengodekan serangan
  dan edge case yang diketahui. Kasus yang dicatat skill itu: CVE-2024-42459 (EdDSA
  signature malleability — appending/removing zeros), CVE-2024-42460 (ECDSA DER encoding —
  invalid bit placement), CVE-2024-42461 (ECDSA DER encoding — leading zero in length
  field). Terapkan saat mengaudit kode kripto/signature di kontrak atau off-chain.
- **zeroize-audit** (registry: `zeroize-audit`): audit penghapusan secret dari memori.
  Confidence gating: finding butuh >=2 sinyal independen untuk `confirmed` (1 sinyal =
  `likely`, 0 sinyal kuat = `needs_review`); sinyal: name pattern, type hint, anotasi,
  bukti IR/ASM, MCP cross-reference, CFG, validasi PoC. 11 kategori finding C/C++ didukung
  PoC; untuk Rust hanya MISSING_SOURCE_ZEROIZE, SECRET_COPY, PARTIAL_WIPE yang didukung
  PoC. Finding tertentu TIDAK PERNAH valid tanpa bukti compiler (IR/ASM diff).
  PoC di-compile/run lokal atas kode yang diaudit; artefak di /tmp/zeroize-audit-{run_id}/.
- **mermaid-to-proverif** (registry: `mermaid-to-proverif`): pemodelan protokol ke ProVerif
  untuk verifikasi formal properti keamanan protokol — pakai untuk invarian protokol
  (bukan sekadar review kode).
