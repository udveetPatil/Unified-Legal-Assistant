import json
from datasets import load_from_disk

dataset = load_from_disk("data/raw/constitution_qa/dataset")
records = [dict(row) for row in dataset["train"]]

with open("data/raw/constitution_qa/constitution_qa.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Saved {len(records)} records to constitution_qa.json")