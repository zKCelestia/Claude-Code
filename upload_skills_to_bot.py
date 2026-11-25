"""Upload skill dari .claude/skills/ ke Skills API akun Anthropic-mu, supaya bisa
dipakai oleh agent bot Telegram.

PERINGATAN:
- Ini membuat objek skill PERMANEN di akunmu (ratusan). Hapus lewat Console bila perlu.
- Memakai kredit API dan butuh waktu (ada jeda anti rate-limit).
- Jalankan SEKALI. Script ini idempoten: skill yang sudah diupload dilewati
  (dicatat di uploaded_skills.json), jadi aman diulang kalau terputus.

Jalankan:
  export ANTHROPIC_API_KEY=sk-ant-...   # atau `ant auth login`
  python upload_skills_to_bot.py        # semua skill valid
  python upload_skills_to_bot.py nama1 nama2   # hanya skill tertentu

Setelah selesai, jalankan `python setup_agent.py` agar agent memakai skill-skill ini.
"""

import json
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

BASE = Path(__file__).parent
SKILLS_DIR = BASE / ".claude" / "skills"
MANIFEST = BASE / "uploaded_skills.json"

# Batas aman per skill: Skills API menolak paket yang terlalu besar/banyak file.
MAX_FILES_PER_SKILL = 60
MAX_SKILL_BYTES = 18 * 1024 * 1024
SKIP_SUFFIXES = {".mp4", ".mov", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".pdf"}


def gather_files(skill_dir: Path):
    """Semua file skill sebagai (relative_path, bytes). SKILL.md harus di root."""
    files, total = [], 0
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(skill_dir).as_posix()
        if rel != "SKILL.md" and p.suffix.lower() in SKIP_SUFFIXES:
            continue  # aset berat (video/font/gambar) dilewati agar paket kecil
        data = p.read_bytes()
        total += len(data)
        files.append((rel, data))
    return files, total


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()

    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    only = set(sys.argv[1:])

    dirs = [d for d in sorted(SKILLS_DIR.iterdir()) if (d / "SKILL.md").is_file()]
    if only:
        dirs = [d for d in dirs if d.name in only]

    done = skipped = failed = 0
    for d in dirs:
        name = d.name
        if name in manifest:
            skipped += 1
            continue

        files, total = gather_files(d)
        if not any(rel == "SKILL.md" for rel, _ in files):
            print(f"[lewati] {name}: tidak ada SKILL.md di root")
            failed += 1
            continue
        if len(files) > MAX_FILES_PER_SKILL or total > MAX_SKILL_BYTES:
            print(f"[lewati] {name}: terlalu besar ({len(files)} file, {total//1024} KB)")
            failed += 1
            continue

        for attempt in range(4):
            try:
                skill = client.skills.create(files=files, display_name=name)
                manifest[name] = skill.id
                MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))
                done += 1
                print(f"[ok]   {name} -> {skill.id}  ({done} selesai)")
                time.sleep(0.4)  # ramah rate-limit
                break
            except anthropic.RateLimitError:
                wait = 2 ** attempt * 3
                print(f"[rate] {name}: tunggu {wait}s")
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                print(f"[gagal] {name}: {e.status_code} {getattr(e, 'message', '')}")
                failed += 1
                break
        else:
            print(f"[gagal] {name}: rate limit terus")
            failed += 1

    print(f"\nSelesai. Baru diupload: {done}, sudah ada: {skipped}, gagal: {failed}")
    print(f"Total skill terdaftar: {len(manifest)} (lihat {MANIFEST.name})")
    print("Berikutnya: jalankan `python setup_agent.py` untuk memasang skill ke agent.")


if __name__ == "__main__":
    main()
