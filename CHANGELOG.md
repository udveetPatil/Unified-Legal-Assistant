# Changelog

All notable changes to the Unified Legal Assistant project are recorded here.

---

## [2026-09-29] - Retrieval Pipeline: Legal Type + Hybrid + Re-ranker

### What Changed
- `src/classifier/intent.py`: Added `legal_type` field (substantive/procedural/unclear) using keyword scoring
- `src/vector_db/retriever.py`: Added source-aware filtering based on `legal_type`
- `src/vector_db/bm25_retriever.py`: Mirrored the same filter logic for keyword search
- `src/vector_db/hybrid.py`: New file. Combines vector + BM25 results using Reciprocal Rank Fusion (RRF)
- `src/vector_db/reranker.py`: New file. Cross-encoder re-ranker using `cross-encoder/ms-marco-MiniLM-L-6-v2`
- `src/pipeline.py`: New file. Orchestrates classify → hybrid → re-rank

### Why
- Initial retrieval was polluted: CrPC QA (8,194 records) dominated every query, burying substantive BNS/IPC answers
- Vector search alone could not distinguish procedural vs substantive questions
- BM25 alone could not rank precise answers above near-misses
- Cross-encoder provides the accuracy that neither embedding similarity nor keyword matching can achieve

### Output
**Before (Vector only, "punishment for murder"):**
1. CrPC QA (wrong source)
2. CrPC QA (wrong source)
3. CrPC QA (wrong source)
4. BNS Section 105 (near-miss)
5. CrPC QA (wrong source)

**After (Hybrid + Re-ranker, "punishment for murder"):**
1. **BNS Section 103 (correct)**
2. BNS Section 105
3. BNS Section 109
4. BNS Section 230
5. BNS Section 110

**After (Procedural query, "how do I file an FIR?"):**
1. CrPC QA (correct)
2. CrPC QA
3. CrPC QA
4. CrPC QA
5. CrPC QA

**After (Temporal query, "punishment for murder in 2010"):**
- Pending fix. Should return IPC Section 302 but currently returns BNS Section 103.

---

## [2026-09-28] - Vector DB Build

### What Changed
- `src/vector_db/build_index.py`: New file. Builds ChromaDB collection from GSMS-B, GovIntel sections, and CrPC QA.

### Why
- Needed a semantic search index over all criminal law data.

### Output
- Collection: `criminal`
- Documents: 14,548
- Sources: gsms-b (6,354), govintel_sections (1,605), crpc_qa (8,194)

---

## [2026-09-28] - Intent Classifier

### What Changed
- `src/classifier/intent.py`: New file. Extracts domain, act, section_number, question_type, is_temporal, complexity from a user query.

### Why
- The query pipeline needs structured signals to apply filters and route queries correctly.

### Output
- All 6 test queries classified correctly (domain, act, section, temporal flag, complexity).

---

## [2026-09-27] - Data Acquisition Complete

### What Changed
- Downloaded: GSMS-B, InIRAC, GovIntel, CrPC/IEA, Constitution QA, CPA 2019.

### Why
- Core data for Criminal, Constitutional, and Consumer law.

### Output
| Domain | Statutory Text | QA Pairs | Temporal | Judgments |
|--------|---------------|----------|----------|-----------|
| Criminal (new) | BNS/BNSS/BSA | 6,354 | GovIntel | 511 |
| Criminal (old) | IPC/CrPC/IEA | CrPC QA | GovIntel | 511 |
| Constitutional | In QA form | 3,311 | N/A | In QA |
| Consumer | CPA 2019 (163) | None | N/A | None |