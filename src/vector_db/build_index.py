"""
Build the Vector Database for Criminal Law (Tier 1).

Loads:
  - GSMS-B combined QA (6,354 pairs)
  - GovIntel sections (BNS, BNSS, BSA, IPC)
  - CrPC QA (procedure law)

Embeds each record using sentence-transformers (all-MiniLM-L6-v2)
Stores in ChromaDB collection: criminal

Output: data/processed/vector_db/criminal/
"""

import json
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ============================================================
# Configuration
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
VECTOR_DB_PATH = PROJECT_ROOT / "data" / "processed" / "vector_db"
COLLECTION_NAME = "criminal"
EMBED_MODEL = "all-MiniLM-L6-v2"

VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Vector DB Build: Criminal Law")
print("=" * 60)

# ============================================================
# Step 1: Load embedding model
# ============================================================
print("\n[1/5] Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)
print(f"  Model loaded. Dimension: {model.get_embedding_dimension()}")

# ============================================================
# Step 2: Load GSMS-B combined QA
# ============================================================
print("\n[2/5] Loading GSMS-B QA pairs...")
gsms_path = DATA_RAW / "gsms-b" / "bns_bnss_bsa_combined_legal_qa.jsonl"

gsms_records = []
with open(gsms_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        gsms_records.append(json.loads(line))

print(f"  Loaded {len(gsms_records)} QA pairs")

# ============================================================
# Step 3: Load GovIntel sections
# ============================================================
print("\n[3/5] Loading GovIntel section text...")
sections_dir = DATA_RAW / "govintel" / "sections"

section_files = {
    "BNS 2023": "bns_sections.json",
    "BNSS 2023": "bnss_sections.json",
    "BSA 2023": "bsa_sections.json",
    "IPC 1860": "ipc_sections.json",
}

govintel_sections = []
for act_name, filename in section_files.items():
    filepath = sections_dir / filename
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found. Skipping.")
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    count_before = len(govintel_sections)

    if isinstance(data, list):
        for item in data:
            govintel_sections.append({
                "act": act_name,
                "section_number": str(item.get("section_number", "")),
                "section_title": item.get("section_title", ""),
                "text": item.get("section_text", ""),
                "source": "govintel_sections",
            })
    elif isinstance(data, dict):
        for key, value in data.items():
            govintel_sections.append({
                "act": act_name,
                "section_number": key,
                "section_title": "",
                "text": value if isinstance(value, str) else json.dumps(value),
                "source": "govintel_sections",
            })

    count_after = len(govintel_sections)
    print(f"  {act_name}: {count_after - count_before} sections")

print(f"  Total GovIntel sections: {len(govintel_sections)}")

# ============================================================
# Step 4: Load CrPC QA
# ============================================================
print("\n[4/5] Loading CrPC QA...")
crpc_qa_path = DATA_RAW / "crpc_iea" / "crpc_qa.json"

crpc_records = []
if crpc_qa_path.exists():
    with open(crpc_qa_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            crpc_records = data
        elif isinstance(data, dict):
            for key, value in data.items():
                crpc_records.append({"question": key, "answer": value})
    print(f"  Loaded {len(crpc_records)} CrPC QA pairs")
else:
    print(f"  WARNING: {crpc_qa_path} not found. Skipping.")

# ============================================================
# Step 5: Build ChromaDB collection
# ============================================================
print("\n[5/5] Building ChromaDB collection...")

client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

try:
    client.delete_collection(COLLECTION_NAME)
    print(f"  Deleted existing collection: {COLLECTION_NAME}")
except Exception:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)
print(f"  Created collection: {COLLECTION_NAME}")

documents = []
metadatas = []
ids = []
doc_id = 0

# ----- GSMS-B QA pairs -----
for record in gsms_records:
    question = record.get("question", "")
    answer = record.get("answer", "")
    text = f"Q: {question}\nA: {answer}"
    documents.append(text)
    metadatas.append({
        "source": "gsms-b",
        "act": record.get("act", ""),
        "section_number": record.get("section_number", ""),
        "section_title": record.get("section_title", ""),
        "question_type": record.get("question_type", ""),
        "chunk_id": record.get("chunk_id", f"gsms_{doc_id}"),
    })
    ids.append(f"gsms_{doc_id}")
    doc_id += 1

# ----- GovIntel sections -----
for section in govintel_sections:
    if not section["text"]:
        continue
    text = f"{section['act']} Section {section['section_number']}: {section['section_title']}\n{section['text']}"
    documents.append(text)
    metadatas.append({
        "source": "govintel_sections",
        "act": section["act"],
        "section_number": section["section_number"],
        "section_title": section["section_title"],
    })
    ids.append(f"govintel_{doc_id}")
    doc_id += 1

# ----- CrPC QA -----
for record in crpc_records:
    question = record.get("question", record.get("input", ""))
    answer = record.get("answer", record.get("output", ""))
    if not question or not answer:
        continue
    text = f"Q: {question}\nA: {answer}"
    documents.append(text)
    metadatas.append({
        "source": "crpc_qa",
        "act": "CrPC 1973",
        "section_number": "",
        "section_title": "",
    })
    ids.append(f"crpc_{doc_id}")
    doc_id += 1

print(f"  Total documents to embed: {len(documents)}")

BATCH_SIZE = 256
print(f"  Embedding in batches of {BATCH_SIZE}...")

for i in range(0, len(documents), BATCH_SIZE):
    batch_docs = documents[i:i + BATCH_SIZE]
    batch_meta = metadatas[i:i + BATCH_SIZE]
    batch_ids = ids[i:i + BATCH_SIZE]
    embeddings = model.encode(batch_docs, show_progress_bar=False).tolist()
    collection.add(
        documents=batch_docs,
        embeddings=embeddings,
        metadatas=batch_meta,
        ids=batch_ids,
    )
    print(f"    Batch {i // BATCH_SIZE + 1}: added {len(batch_docs)} records")

print(f"\n  Collection count: {collection.count()}")

# ============================================================
# Verify: count by source and act
# ============================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

from collections import Counter
all_records = collection.get(include=["metadatas"])
sources = Counter(m.get("source") for m in all_records["metadatas"])
acts = Counter(m.get("act") for m in all_records["metadatas"])

print("\nSources:")
for src, count in sources.most_common():
    print(f"  {src}: {count}")

print("\nActs:")
for act, count in acts.most_common():
    print(f"  {act}: {count}")

print("\n" + "=" * 60)
print("VECTOR DB BUILD COMPLETE")
print("=" * 60)