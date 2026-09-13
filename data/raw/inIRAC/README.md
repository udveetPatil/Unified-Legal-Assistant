---
language:
- en
- hi
- bn
license: cc-by-4.0
task_categories:
- question-answering
- text-classification
- summarization
- text-generation
- token-classification
task_ids:
- extractive-qa
- multi-label-classification
tags:
- legal
- indian-law
- knowledge-graph
- IRAC
- procedural-reasoning
- supreme-court
- high-court
- bail
- FalkorDB
- graph-constrained-generation
pretty_name: InIRAC - Indian Legal IRAC Reasoning Dataset
size_categories:
- 100<n<1K
---

# InIRAC: Indian Legal IRAC Reasoning Dataset

InIRAC converts Indian court judgments into structured legal reasoning records using the IRAC framework (Issue, Rule, Application, Conclusion). 
The dataset is designed for legal LLMs, graph-based retrieval systems, and hallucination-resistant judicial AI.

A graph-oriented corpus of Indian Supreme Court and High Court judgments structured around IRAC decomposition with procedural event chains and typed precedent relationships.
IRAC is a widely used legal reasoning methodology taught in common-law legal education worldwide.

InIRAC is designed to support hallucination-resistant legal generation by grounding outputs in typed precedent and procedural graph structures.

Companion dataset to the paper:
**Falkor-IRAC: Graph-Constrained Generation for Verified Legal Reasoning in Indian Judicial AI**

Joy Bose, Independent Researcher, Bengaluru

Arxiv Paper: https://arxiv.org/abs/2605.14665  
Code: https://gitlab.com/joyboseroy/falkor-irac

---

## Dataset Summary

InIRAC provides structured IRAC annotations for Indian court judgments designed for graph-native legal reasoning research. Unlike prior Indian legal NLP datasets that focus on judgment prediction or summarisation, InIRAC is built for:

- **Graph-constrained generation**: each judgment is a node structure in a FalkorDB knowledge graph
- **Procedural reasoning**: litigation flow modelled as state machines with TRIGGERS and PRECEDES relationships
- **Conflict-aware retrieval**: doctrinal conflicts typed as CONFLICTS_WITH with coordinate_bench, per_incuriam, or distinguished subtypes

The v0.1 corpus covers 500+ Supreme Court and High Court judgments spanning 1949-2026, with depth in bail jurisprudence, constitutional rights, service law, and contempt proceedings.

---

## Data Fields

Each record contains:

```json
{
  "case_id": "unique identifier",
  "case_name": "e.g. Kalyan Chandra Sarkar v. Rajesh Ranjan",
  "citation": "e.g. (2004) 7 SCC 528",
  "court": "Supreme Court | Delhi High Court | ...",
  "year": 2004,
  "matter_type": "bail | constitutional | service | criminal | civil | general",
  "bench_size": 2,
  "bench_type": "division | full | constitutional",
  "issues": [{"text": "...", "issue_type": "procedural | substantive | constitutional | evidentiary"}],
  "rules": [{"text": "...", "source": "precedent | statute | custom"}],
  "analysis_summary": "...",
  "conclusion": "...",
  "outcome_type": "allowed | dismissed | modified | remanded",
  "statutes_cited": [{"statute_name": "...", "section_number": "...", "purpose": "relied_upon | distinguished | referred"}],
  "precedents_cited": [{"citation": "...", "case_name": "...", "relationship": "CITES | OVERRULES | DISTINGUISHES | CONFLICTS_WITH", "proposition": "...", "conflict_type": "coordinate_bench | per_incuriam | distinguished"}],
  "procedural_events": ["FIR_FILED", "BAIL_DENIED", "APPEAL_FILED"],
  "extraction_confidence": 0.7,
  "source_url": "https://indiankanoon.org/doc/..."
}
```

## Relationship Types

| Relationship | Description | Novel |
|---|---|---|
| CITES | Case relies on precedent | |
| OVERRULES | Later judgment expressly overrules | |
| DISTINGUISHES | Limits earlier holding on facts | |
| CONFLICTS_WITH | Coordinate bench disagreement (typed) | Yes |
| RESOLVED_BY | Points to larger bench resolution | Yes |
| NARROWED_BY | Prior holding narrowed by later case | Yes |
| TRIGGERS | Procedural event triggers next event | Yes |
| PRECEDES | Temporal ordering of procedural events | Yes |

## Corpus Statistics (v0.1)

| Matter Type | Approx. Cases |
|---|---|
| Bail / Criminal procedure | 200 |
| Constitutional | 80 |
| Service / Employment | 60 |
| General / Civil | 160 |
| **Total** | **~500** |

Temporal span: 1949-2026. Notable cases include Golaknath (1967), Maneka Gandhi (1978), PUDR (1982), Sanjay Chandra (2012), Arnesh Kumar (2014), P. Chidambaram (2019).

## Extraction Pipeline

IRAC annotations were produced in two passes:

**Pass 1 (bulk):** TinyLlama 1B via Ollama. Fast but lightweight metadata-oriented extraction. Typically extracts case name and citation reliably from the page title; IRAC fields (issues, rules, analysis) are often empty or low-confidence. Records from this pass typically have `extraction_confidence` between 0.1 and 0.4.

**Pass 2 (quality):** Mistral 7B-Instruct via Ollama on the same corpus. Produces structured JSON citations and partial IRAC fields on roughly 30-40% of queries; the remainder abstain. Records re-processed with Mistral have `extraction_confidence` between 0.5 and 1.0.

The `extraction_confidence` field in each record indicates extraction quality. Recommended thresholds:

| Confidence | Quality | Recommended use |
|---|---|---|
| 0.8 - 1.0 | High | Full IRAC fields reliable |
| 0.4 - 0.8 | Medium | Case metadata reliable; IRAC fields partial |
| 0.1 - 0.4 | Low (TinyLlama) | Case name and citation only; IRAC fields unreliable |
| < 0.1 | Very low | Metadata only; exclude from IRAC tasks |

For citation grounding and graph traversal tasks, all records are usable regardless of confidence — the case name and source URL are reliable across both extraction passes. For IRAC reasoning tasks, filter to `extraction_confidence >= 0.5`.

## Limitations

- IRAC field quality depends on extraction pass — see Extraction Pipeline above
- Complex constitutional bench judgments consistently produce lower confidence scores due to nested IRAC structures
- English only in v0.1; Hindi/Bengali layer planned for v0.2
- Coverage limited to Supreme Court and selected High Courts; district court and tribunal judgments not included
- Citation relationships are extracted from judgment text, not manually verified against a gold standard

## Example Research Tasks

- Legal IRAC decomposition
- Citation-aware legal RAG
- Conflict-aware precedent retrieval
- Procedural event prediction
- Hallucination detection in legal generation
- Legal knowledge graph construction

## Citation

```bibtex
@dataset{inIRAC2026,
  title  = {InIRAC: Indian Legal IRAC Reasoning Dataset},
  author = {Bose, Joy},
  year   = {2026},
  url    = {https://huggingface.co/datasets/joyboseroy/inIRAC}
}
```

## License

CC BY 4.0. Underlying judgment texts are public domain court documents.
