---
language:
- en
license: apache-2.0
task_categories:
- text-generation
- question-answering
task_ids:
- language-modeling
tags:
- law
- legal
- india
- BNS
- BNSS
- BSA
- criminal-law
- question-answering
- fine-tuning
- instruction-tuning
- jsonl
pretty_name: Indian Legal QA — BNS + BNSS + BSA 2023
size_categories:
- 1K<n<10K
---

<p align="center">
  <img src="assets/banner.png" alt="Indian Legal QA — BNS + BNSS + BSA 2023" width="100%"/>
</p>

<h1 align="center">Indian Legal QA — BNS + BNSS + BSA 2023</h1>

<p align="center">
  <b>6,354 structured question-answer pairs covering all 1,059 sections across India's three criminal justice acts of 2023</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Format-JSONL-2563EB?style=flat-square" alt="JSONL"/>&nbsp;<img src="https://img.shields.io/badge/Total%20QA%20Pairs-6%2C354-2563EB?style=flat-square" alt="QA Pairs"/>&nbsp;<img src="https://img.shields.io/badge/Sections%20Covered-1%2C059-1B2A4A?style=flat-square" alt="Sections"/>&nbsp;<img src="https://img.shields.io/badge/Acts%20Covered-3-2563EB?style=flat-square" alt="Acts"/>&nbsp;<img src="https://img.shields.io/badge/License-Apache%202.0-green?style=flat-square" alt="License"/>
</p>

---

## Overview

This dataset contains **6,354 instruction-format question-answer pairs** in JSONL format, covering every section of India's three criminal justice reform acts enacted in 2023. Each section has exactly 6 questions approaching the same legal provision from different angles, making this suitable for instruction fine-tuning of language models on Indian criminal law.

| Act | Full Name | Replaces | Sections | QA Pairs | File |
|---|---|---|---|---|---|
| **BNS 2023** | Bharatiya Nyaya Sanhita | IPC 1860 | 358 | 2,148 | `bns_legal_qa.jsonl` |
| **BNSS 2023** | Bharatiya Nagarik Suraksha Sanhita | CrPC 1973 | 531 | 3,186 | `bnss_legal_qa.jsonl` |
| **BSA 2023** | Bharatiya Sakshya Adhiniyam | Indian Evidence Act 1872 | 170 | 1,020 | `bsa_legal_qa.jsonl` |
| **Combined** | All three acts | — | 1,059 | 6,354 | `bns_bnss_bsa_combined_legal_qa.jsonl` |

> **Note on data viewer:** The `assets/` folder contains the banner image used in this dataset card. The actual dataset files are the four `.jsonl` files listed above.

---

## Why This Dataset Exists

India's three 2023 criminal justice acts — BNS, BNSS, and BSA — replaced the entire colonial-era criminal justice framework. Existing NLP resources for Indian law are largely focused on the older acts (IPC, CrPC, Indian Evidence Act). This dataset was built to provide structured, section-level QA coverage of the new acts, formatted specifically for instruction fine-tuning of language models. Each question-answer pair is grounded exclusively in the text of the relevant section with a structured citation, making it suitable for building models that can reference specific legal provisions accurately.

---

## Dataset Statistics

| Property | BNS | BNSS | BSA | Combined |
|---|---|---|---|---|
| QA pairs | 2,148 | 3,186 | 1,020 | **6,354** |
| Unique sections | 358 | 531 | 170 | **1,059** |
| Questions per section | 6 | 6 | 6 | **6** |
| Avg question length (words) | 19.7 | 20.8 | 19.4 | **20.2** |
| Avg answer length (words) | 38.5 | 37.3 | 30.8 | **36.7** |

---

## Question Types

Every section in every act has exactly **6 questions**, one of each type:

| Type | What it covers | Example |
|---|---|---|
| `definitional_topic` | Legal concept without mentioning section number | "What is culpable homicide?" |
| `definitional_section` | What a specific numbered section says | "What does Section 100 of BNS 2023 say?" |
| `scenario` | Real-world situation — what law applies? | "If A shoots B intending to kill C, who dies, what offence has A committed?" |
| `elements` | Conditions, requirements, components of a provision | "What are the elements required for theft under BNS 2023?" |
| `exceptions` | Provisos, limitations, carve-outs | "When is private defence not available?" |
| `consequence` | Legal outcomes and practical effects | "What is the punishment for voluntarily causing grievous hurt?" |

---

## Schema

Every row across all four files shares the same schema:

```json
{
  "chunk_id": "BNSS_173",
  "act": "BNSS 2023",
  "section_number": "173",
  "section_title": "Information in cognizable cases",
  "question": "What is a Zero FIR and how does Section 173 of BNSS 2023 enable it?",
  "answer": "A Zero FIR is a First Information Report filed at any police station regardless of jurisdiction. Section 173 of BNSS 2023 enables this by requiring any police station to record the FIR and then transfer it to the police station having jurisdiction over the area where the offence was committed. [Source: Section 173, BNSS 2023]",
  "question_type": "definitional_section"
}
```

| Field | Type | Description |
|---|---|---|
| `chunk_id` | string | `BNS_`, `BNSS_`, or `BSA_` + section number |
| `act` | string | `"BNS 2023"`, `"BNSS 2023"`, or `"BSA 2023"` |
| `section_number` | string | Section number as in the act |
| `section_title` | string | Official section title |
| `question` | string | The question — use as model input |
| `answer` | string | The answer with citation — use as model output |
| `question_type` | string | One of the 6 types listed above |

---

## How to Use

### Load the combined dataset
```python
from datasets import load_dataset

dataset = load_dataset(
    "GSMS-B/Indian-Legal-QA-BNS-BNSS-BSA",
    data_files="bns_bnss_bsa_combined_legal_qa.jsonl",
    split="train"
)
print(f"Total rows: {len(dataset)}")
```

### Load a specific act only
```python
# BNS only
bns = load_dataset(
    "GSMS-B/Indian-Legal-QA-BNS-BNSS-BSA",
    data_files="bns_legal_qa.jsonl",
    split="train"
)

# BNSS only
bnss = load_dataset(
    "GSMS-B/Indian-Legal-QA-BNS-BNSS-BSA",
    data_files="bnss_legal_qa.jsonl",
    split="train"
)

# BSA only
bsa = load_dataset(
    "GSMS-B/Indian-Legal-QA-BNS-BNSS-BSA",
    data_files="bsa_legal_qa.jsonl",
    split="train"
)
```

### Format for instruction fine-tuning
```python
EOS_TOKEN = tokenizer.eos_token

def format_sample(example):
    prompt = f"""Below is a question about Indian criminal law. Answer accurately based on the relevant legal provision.

### Instruction:
{example['question']}

### Response:
{example['answer']}{EOS_TOKEN}"""
    return {"text": prompt}

dataset = dataset.map(format_sample)
```

> **Important:** Use only `question` and `answer` fields in your training prompt. The fields `chunk_id`, `act`, `section_number`, `section_title`, and `question_type` are for filtering and metadata — including them in the prompt causes the model to expect them at inference time.

---

## Grounding Policy

Every answer is grounded exclusively in the text of the section it references. No outside legal doctrine, no cross-section inference. Every answer ends with a structured citation:

```
[Source: Section <number>, <ACT> 2023]
```

---

## Files in This Repository

```
Indian-Legal-QA-BNS-BNSS-BSA/
├── assets/
│   └── banner.png                              ← banner image (not a dataset file)
├── bns_bnss_bsa_combined_legal_qa.jsonl        ← all 6,354 rows combined
├── bns_legal_qa.jsonl                          ← BNS 2023 only (2,148 rows)
├── bnss_legal_qa.jsonl                         ← BNSS 2023 only (3,186 rows)
├── bsa_legal_qa.jsonl                          ← BSA 2023 only (1,020 rows)
└── README.md                                   ← this file
```

---

## Models Fine-tuned on `bns_bnss_bsa_combined_legal_qa.jsonl`

### Llama 3.2 — 3B
| Repo | Type |
|---|---|
| [GSMS-B/Indian-Legal-Llama-3.2-3B](https://huggingface.co/GSMS-B/Indian-Legal-Llama-3.2-3B) | Merged full model |
| [GSMS-B/Indian-Legal-Llama-3.2-3B-Adapter](https://huggingface.co/GSMS-B/Indian-Legal-Llama-3.2-3B-Adapter) | LoRA adapter |
| [GSMS-B/Indian-Legal-Llama-3.2-3B-GGUF](https://huggingface.co/GSMS-B/Indian-Legal-Llama-3.2-3B-GGUF) | GGUF (quantized) |

### Qwen 2.5 — 3B
| Repo | Type |
|---|---|
| [GSMS-B/Indian-Legal-Qwen2.5-3B](https://huggingface.co/GSMS-B/Indian-Legal-Qwen2.5-3B) | Merged full model |
| [GSMS-B/Indian-Legal-Qwen2.5-3B-Adapter](https://huggingface.co/GSMS-B/Indian-Legal-Qwen2.5-3B-Adapter) | LoRA adapter |
| [GSMS-B/Indian-Legal-Qwen2.5-3B-GGUF](https://huggingface.co/GSMS-B/Indian-Legal-Qwen2.5-3B-GGUF) | GGUF (quantized) |

### Qwen 2.5 — 1.5B
| Repo | Type |
|---|---|
| [GSMS-B/Indian-Legal-Qwen2.5-1.5B](https://huggingface.co/GSMS-B/Indian-Legal-Qwen2.5-1.5B) | Merged full model |
| [GSMS-B/Indian-Legal-Qwen2.5-1.5B-Adapter](https://huggingface.co/GSMS-B/Indian-Legal-Qwen2.5-1.5B-Adapter) | LoRA adapter |
| [GSMS-B/Indian-Legal-Qwen2.5-1.5B-GGUF](https://huggingface.co/GSMS-B/Indian-Legal-Qwen2.5-1.5B-GGUF) | GGUF (quantized) |

---

## Related Resources

| Resource | Link |
|---|---|
| Source sections dataset | [GSMS-B/indian-legal-sections-bns-bnss-bsa-2023](https://huggingface.co/datasets/GSMS-B/indian-legal-sections-bns-bnss-bsa-2023) |

---

## Author

**GSMS-B** — Bugatha Ganasyam Mani Sankar  
B.Tech CSE, JNTU-GV College of Engineering, Vizianagaram

---

## License

Released under [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).  
The underlying legal text (BNS, BNSS, BSA 2023) consists of Government of India public documents.

> **Disclaimer:** This dataset is for research and educational purposes only. It is training data for question-answering and instruction-tuning based fine-tuning approaches. It does not constitute legal advice. Consult a qualified lawyer for legal matters.