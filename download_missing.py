"""
Download missing datasets for Unified Legal Assistant for India.
Fills gaps: CrPC, IEA, Constitution QA, Consumer Law.
"""
import os
import requests
from huggingface_hub import hf_hub_download

# ----- Create target folders -----
folders = ["data/raw/crpc_iea", "data/raw/constitution_qa", "data/raw/consumer"]
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Created: {folder}")

# ============================================================
# 1. CrPC + IEA raw text (civictech-India GitHub)
# ============================================================
print("\n[1/4] Downloading CrPC and IEA raw text...")
GITHUB_BASE = "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main"
files_to_download = {
    "crpc.json": "data/raw/crpc_iea/crpc.json",
    "iea.json": "data/raw/crpc_iea/iea.json",
}
for filename, dest in files_to_download.items():
    try:
        response = requests.get(f"{GITHUB_BASE}/{filename}", timeout=30)
        response.raise_for_status()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"  Downloaded: {dest}")
    except Exception as e:
        print(f"  FAILED: {filename} -> {e}")

# ============================================================
# 2. CrPC QA pairs (Techmaestro369 Hugging Face)
# ============================================================
print("\n[2/4] Downloading CrPC QA pairs...")
try:
    path = hf_hub_download(
        repo_id="Techmaestro369/indian-legal-texts-finetuning",
        filename="crpc_qa.json",
        repo_type="dataset",
        local_dir="data/raw/crpc_iea",
    )
    print(f"  Downloaded: {path}")
except Exception as e:
    print(f"  FAILED: {e}")

# ============================================================
# 3. Constitution QA (nisaar Hugging Face)
# ============================================================
print("\n[3/4] Downloading Constitution QA...")
try:
    path = hf_hub_download(
        repo_id="nisaar/Articles_Constitution_3300_Instruction_Set",
        filename="train.json",
        repo_type="dataset",
        local_dir="data/raw/constitution_qa",
    )
    print(f"  Downloaded: {path}")
except Exception as e:
    print(f"  FAILED: {e}")

# ============================================================
# 4. Consumer Law (Grahak-Nyay GitHub)
# ============================================================
print("\n[4/4] Downloading Consumer Law data...")
GRAHAK_BASE = "https://raw.githubusercontent.com/ShreyGanatra/GrahakNyay/main"
consumer_files = {
    "data/GeneralQA.json": "data/raw/consumer/general_qa.json",
    "data/SectoralQA.json": "data/raw/consumer/sectoral_qa.json",
}
for src, dest in consumer_files.items():
    try:
        response = requests.get(f"{GRAHAK_BASE}/{src}", timeout=30)
        response.raise_for_status()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"  Downloaded: {dest}")
    except Exception as e:
        print(f"  WARNING: {src} not found -> {e}")

print("\n" + "=" * 50)
print("DOWNLOAD COMPLETE")
print("=" * 50)