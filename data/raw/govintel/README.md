---
license: cc-by-nc-4.0
language:
  - en
tags:
  - legal
  - india
  - criminal-law
  - knowledge-graph
  - fine-tuning
  - BNS
  - BNSS
  - BSA
  - IPC
  - temporal-reasoning
  - multi-agent
  - neurosymbolic
size_categories:
  - 10K<n<100K
task_categories:
  - question-answering
  - text-generation
  - information-retrieval
pretty_name: "GovIntel Legal Dataset: Indian Criminal Law 2023"
---

# GovIntel Legal Dataset

India's first structured dataset and temporal knowledge graph for the 2023 Indian criminal law reform (BNS, BNSS, BSA) and its predecessor statutes (IPC, CrPC, Evidence Act).

Built for GovIntel (Retrieval-Augmented Debate with Neurosymbolic Verification), a multi-agent legal reasoning system with temporal awareness, graph-based retrieval and structured argumentation.

---

## Statute Coverage

| Statute | Full Name | Sections | Effective From | Replaces |
|---------|-----------|----------|----------------|----------|
| BNS 2023 | Bharatiya Nyaya Sanhita | 358 | July 1, 2024 | IPC 1860 |
| BNSS 2023 | Bharatiya Nagarik Suraksha Sanhita | 531 | July 1, 2024 | CrPC 1973 |
| BSA 2023 | Bharatiya Sakshya Adhiniyam | 171 | July 1, 2024 | Evidence Act 1872 |
| IPC 1860 | Indian Penal Code | 545 | 1860 | still governs pre-July 2024 acts |

**Temporal rule**: Acts committed before July 1, 2024 are governed by IPC/CrPC/Evidence Act. Acts on or after July 1, 2024 are governed by BNS/BNSS/BSA. This transition is the core challenge the dataset is built to test.

---

## Dataset Statistics

| Metric | Value |
|--------|-------|
| Total training pairs | 14,280 |
| Train split | 12,859 (90%) |
| Eval split | 1,421 (10%) |
| Deduplication | First 800 characters of instruction |
| Split strategy | Stratified by task type |

---

## Task Type Breakdown

| Task Type | Count | Description |
|-----------|-------|-------------|
| section_explanation | 4,655 | What a given section provides, in plain language |
| principle_qa | 3,296 | Legal principles from Supreme Court judgments |
| temporal_law_application | 1,328 | IPC vs BNS routing based on offense date |
| bns_seed_doctrinal | 330 | Definitional questions on BNS sections |
| bns_seed_interpretive | 330 | Ambiguous scenario interpretation |
| bns_seed_relational | 330 | Multi-section interaction questions |
| bns_seed_scenario | 330 | Fact-pattern application using IRAC structure |
| bns_seed_temporal | 346 | IPC to BNS transition questions |
| offense_ingredients | 1,066 | Mens rea, actus reus, and aggravating elements |
| cross_code_profile | 537 | BNS offense linked with BNSS procedure and BSA evidence rules |
| punishment_and_defenses | 303 | Penalties, exceptions, and available defenses |
| procedural_deep_dive | 276 | BNSS arrest, bail, and trial procedure |
| judgment_summary | 478 | Facts and rulings from Supreme Court cases |
| judgment_grounded | 71 | Applying judgment reasoning to new fact patterns |
| offense_elements | 310 | Element-by-element offense breakdown |

Cross-code questions require simultaneous reasoning across BNS (substantive offense), BNSS (procedure), and BSA (evidence), a combination absent from all existing Indian legal datasets.

---

## Knowledge Graph

### Nodes

| Type | Count |
|------|-------|
| BNS sections | 358 |
| BNSS sections | 531 |
| BSA sections | 171 |
| IPC sections | 545 |
| Legal principles | 1,587 |
| Total | 3,192 |

### Edges

| Category | Count | Types |
|----------|-------|-------|
| Semantic / Deterministic | 1,274 | IPC_TEMPORAL_PAIR (512), CHAPTER_ADJACENT (338), DEFINITION_DEPENDENCY (258), EXPLICIT_REFERENCE (144), PUNISHMENT_PAIR (19), PENALTY_REFERENCE (3) |
| Cross-Code | 484 | CROSS_CODE_PROCEDURE, CROSS_CODE_EVIDENCE across BNS, BNSS, BSA, IPC |
| Judgment | 1,765 | JUDGMENT_INTERPRETS (1,713), JUDGMENT_PRIMARILY_INTERPRETS (52) |
| Autonomous | 163 | ANALOGOUS_OFFENSE (34), CROSS_REFERENCE (25), OVERLAPPING_SECTION (24), DEFENSE_APPLICABILITY (20), MENS_REA_GRADIENT (19), ESCALATION_CHAIN (14), SENTENCING_CLUSTER (14), ABETMENT_OVERLAY (13) |
| IPC to BNS Mappings | 619 | Temporal successor links |
| Total | 4,305 | |

The 163 autonomous edges were discovered by Kimi K2.5 using function-calling tools (get_section_text, get_neighbors, propose_edge) that let it explore the graph and propose non-obvious semantic connections. These capture mens rea gradients, escalation chains, and cross-statute analogies that deterministic rules would miss.

---

## Format

Each record is a chat-formatted training example compatible with OpenAI and Anthropic APIs:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a legal expert specializing in Indian criminal law (BNS 2023, BNSS 2023, BSA 2023, IPC 1860). Provide accurate answers with proper legal citations and IRAC reasoning."
    },
    {
      "role": "user",
      "content": "What does Section 103 of the BNS 2023 provide?"
    },
    {
      "role": "assistant",
      "content": "Section 103 of the Bharatiya Nyaya Sanhita 2023 defines murder and prescribes punishment. Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. The elements follow from Section 101, which defines culpable homicide as murder when caused with intention to cause death, intention to cause bodily injury likely to cause death, or knowledge that the act is likely to cause death. The IPC equivalent is Section 302, which governed acts committed before July 1, 2024."
    }
  ]
}
```

---

## Fine-Tuned Model

Base model: Llama 3.3 70B Instruct, fine-tuned on Fireworks AI.
Training: 2 epochs, LoRA rank 16, learning rate 1e-4, 65,536 token context window, 12,859 training pairs.

### Benchmark Results (50-question evaluation)

| Model | Overall | Factual Accuracy | Temporal Routing | Legal Reasoning | Section Match F1 | IRAC Quality |
|-------|---------|------------------|------------------|-----------------|------------------|--------------|
| GovIntel Fine-tuned (Llama 3.3 70B) | 7.09 | 6.26 | 9.77 | 6.40 | 0.854 | 3.98 |
| GPT OSS 120B | 5.48 | 3.66 | 9.23 | 4.96 | 0.439 | 2.46 |
| Kimi K2.5 | 5.43 | 4.70 | 9.36 | 5.04 | 0.878 | 2.08 |
| Llama 3.3 70B Base | 5.31 | 4.09 | 8.91 | 4.47 | 0.415 | 1.98 |

Improvements of the fine-tuned model over base Llama 3.3 70B: temporal routing +0.86, section citation F1 +0.439, IRAC quality +2.00, overall score +1.78.

---

## Quick Start

```python
from datasets import load_dataset

ds = load_dataset("aashnasharma/govintel-legal-dataset")
print(ds["train"][0])
```

---

## Citation

```bibtex
@dataset{govintel2026,
  title={GovIntel Legal Dataset: Structured Knowledge Graph and Training Data for Indian Criminal Law Reform 2023},
  author={Sharma, Aashna and Mangla, Harshvir},
  year={2026},
  publisher={Hugging Face},
  howpublished={\url{https://huggingface.co/datasets/aashnasharma/govintel-legal-dataset}},
  note={Dataset for GovIntel: Retrieval-Augmented Debate with Neurosymbolic Verification}
}
```

---

## License

CC BY-NC 4.0 (Attribution-NonCommercial). Free for research, education, and non-commercial use. Commercial use requires permission. The underlying statutes are public domain (Government of India). Supreme Court judgments are public domain via Indiankanoon.org.

---

## Acknowledgments

Data sources: India Code (indiacode.nic.in), Indiankanoon.org, NCRB Sankalan Portal.
Models: Kimi K2.5 (Moonshot AI), Llama 3.3 70B (Meta), Fireworks AI platform.

Built by Aashna Sharma and Harshvir Mangla at NIT Jalandhar, 2026.
Project: GovIntel, India's first multi-agent legal reasoning system with temporal awareness.
