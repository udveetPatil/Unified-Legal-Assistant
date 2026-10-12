"""
fix_missing_ipc.py — Fill missing IPC sections from civictech-India.

Downloads civictech-India ipc.json, converts to GovIntel schema,
merges the missing sections into ipc_sections.json.
"""

import json
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parent
IPC_PATH = BASE / "data" / "raw" / "govintel" / "sections" / "ipc_sections.json"
CIVIC_URL = "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/ipc.json"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
         "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII",
         "XXIX", "XXX", "XXXI", "XXXII", "XXXIII", "XXXIV", "XXXV"]


def chapter_to_code(chapter) -> str:
    """Convert chapter number to 'CHAPTER I', 'CHAPTER II', etc."""
    if chapter is None:
        return ""
    try:
        n = int(chapter)
        if 0 < n < len(ROMAN):
            return f"CHAPTER {ROMAN[n]}"
        return f"CHAPTER {n}"
    except (ValueError, TypeError):
        return ""


def normalize(num) -> str:
    """Normalize section number for comparison."""
    return str(num).strip().upper().lstrip("0") or "0"


def convert(item: dict) -> dict:
    """Convert civictech record to GovIntel schema."""
    num = item.get("Section", "")
    num_str = str(num).strip().upper()
    return {
        "act": "Indian Penal Code",
        "year": 1860,
        "chapter_code": chapter_to_code(item.get("chapter")),
        "chapter_title": item.get("chapter_title", "").strip().title(),
        "section_number": num,
        "section_id": f"IPC_1860_SEC_{num_str.zfill(3)}",
        "section_title": item.get("section_title", "").strip(),
        "section_text": item.get("section_desc", "").strip(),
    }


# ──────────────────────────────────────────────
# Step 1: Load existing
# ──────────────────────────────────────────────
print("Loading existing IPC sections...")
existing = json.loads(IPC_PATH.read_text(encoding="utf-8"))
print(f"  Existing: {len(existing)} sections")

existing_numbers = {normalize(s.get("section_number", "")) for s in existing}


# ──────────────────────────────────────────────
# Step 2: Download civictech
# ──────────────────────────────────────────────
print("\nDownloading civictech-India ipc.json...")
response = requests.get(CIVIC_URL, timeout=60)
response.raise_for_status()
civic_data = response.json()
print(f"  Downloaded: {len(civic_data)} sections")


# ──────────────────────────────────────────────
# Step 3: Convert + merge
# ──────────────────────────────────────────────
added = []
for item in civic_data:
    num = normalize(item.get("Section", ""))
    if not num or num in existing_numbers:
        continue
    existing.append(convert(item))
    existing_numbers.add(num)
    added.append(str(item.get("Section", "")))

print(f"\nAdded {len(added)} missing sections:")
for num in sorted(added, key=lambda x: (len(x), x)):
    print(f"  IPC {num}")


# ──────────────────────────────────────────────
# Step 4: Save
# ──────────────────────────────────────────────
IPC_PATH.write_text(
    json.dumps(existing, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"\nSaved {len(existing)} sections to {IPC_PATH}")

# ──────────────────────────────────────────────
# Step 5: Sanity check
# ──────────────────────────────────────────────
print("\n=== Sanity Check ===")
for check in ["498A", "120B", "304B", "124A", "153A"]:
    found = [s for s in existing if str(s.get("section_number", "")).upper() == check]
    status = "✅" if found else "❌"
    print(f"  IPC {check:<6} {status}")