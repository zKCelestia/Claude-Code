"""Setup sekali jalan: membuat Environment + Agent di Claude Managed Agents.

Jalankan:  python setup_agent.py
ID hasilnya disimpan ke agent_config.json dan dipakai ulang oleh bot.py.
Kalau agent sudah ada, script ini MEMPERBARUI agent (versi baru), bukan membuat ulang.
"""

import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

CONFIG_PATH = Path(__file__).with_name("agent_config.json")

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """Kamu adalah asisten AI serba guna yang diajak chat lewat Telegram.

- Jawab dalam bahasa yang dipakai pengguna (biasanya Bahasa Indonesia).
- Jawaban ringkas dan enak dibaca di layar HP; pakai daftar singkat bila membantu.
- Telegram menampilkan teks polos: hindari tabel Markdown dan heading.
- Kamu punya workspace sendiri (bash, file, Python). Pakai untuk menghitung,
  mengolah data, atau menulis dan menjalankan kode bila itu membuat jawaban lebih tepat.
- Kalau tidak tahu atau tidak yakin, katakan terus terang.

File:
- File yang dikirim pengguna ada di /mnt/session/uploads/ (path persisnya disebut di pesan).
- Kamu punya skill untuk Excel (xlsx), Word (docx), PowerPoint (pptx) dan PDF.
  Saat pengguna minta membuat atau mengubah dokumen, tulis hasil akhirnya ke
  /mnt/session/outputs/ dengan nama file yang jelas. Semua file di folder itu otomatis
  dikirim ke pengguna di Telegram, jadi jangan taruh file sementara di sana.
- Setelah membuat file, sebutkan singkat isinya; tidak perlu menempelkan isi file di chat.
"""

TOOLS = [
    {
        "type": "agent_toolset_20260401",
        "default_config": {"enabled": True, "permission_policy": {"type": "auto"}},
        "configs": [
            # Akses web dimatikan secara default. Lihat README untuk cara menyalakannya.
            {"name": "web_fetch", "enabled": False},
            {"name": "web_search", "enabled": False},
        ],
    },
]


# Skill bawaan Anthropic. Tambah skill buatan sendiri dengan
# {"type": "custom", "skill_id": "skill_..."} (lihat README).
SKILLS = [
    {"type": "anthropic", "skill_id": "xlsx"},
    {"type": "anthropic", "skill_id": "docx"},
    {"type": "anthropic", "skill_id": "pptx"},
    {"type": "anthropic", "skill_id": "pdf"},
]


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()

    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}

    if "environment_id" not in config:
        environment = client.beta.environments.create(
            name="telegram-assistant-env",
            config={
                "type": "cloud",
                "networking": {
                    "type": "limited",
                    "allow_package_managers": True,
                    "allow_mcp_servers": True,
                },
            },
        )
        config["environment_id"] = environment.id
        print(f"Environment dibuat: {environment.id}")
    else:
        print(f"Environment sudah ada: {config['environment_id']}")

    if "agent_id" not in config:
        agent = client.beta.agents.create(
            name="Telegram Assistant",
            model=MODEL,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            skills=SKILLS,
        )
        print(f"Agent dibuat: {agent.id} (versi {agent.version})")
    else:
        current = client.beta.agents.retrieve(config["agent_id"])
        agent = client.beta.agents.update(
            config["agent_id"],
            version=current.version,
            model=MODEL,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            skills=SKILLS,
        )
        print(f"Agent diperbarui: {agent.id} (versi {agent.version})")

    config["agent_id"] = agent.id
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    print(f"Tersimpan di {CONFIG_PATH.name}")


if __name__ == "__main__":
    main()
