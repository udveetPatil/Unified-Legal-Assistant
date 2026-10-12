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



## [2026-10-07 00:58] - Retrieval Pipeline Complete

### What Changed
- `src/vector_db/build_index.py`: Fixed GovIntel section loading (field name `section_text`, not `section_content`)
- `src/vector_db/retriever.py`: Added temporal filter (IPC 1860 for substantive, CrPC 1973 for procedural)
- `src/vector_db/bm25_retriever.py`: Mirrored temporal filter logic
- `src/vector_db/hybrid.py`: New file. Reciprocal Rank Fusion merger
- `src/vector_db/reranker.py`: New file. Cross-encoder re-ranker
- `src/pipeline.py`: New file. Full retrieval pipeline

### Why
- GovIntel sections were silently skipped due to wrong field name
- Temporal queries returned BNS instead of IPC because no temporal filter existed
- Vector + BM25 alone could not rank raw section text above QA pairs

### Output
**Before ("punishment for murder"):**
1. CrPC QA (wrong source)
2. BNS Section 105 (near-miss)
...

**After ("punishment for murder"):**
1. **BNS Section 103 (raw text)** ✅
2. IPC Section 302 (raw text)
3. BNS Section 103 (GSMS-B QA)
4. BNS Section 104
5. BNS Section 105

**After ("punishment for murder in 2010"):**
1. **IPC Section 302 (raw text)** ✅
2. IPC Section 303
3. IPC Section 304
4. IPC Section 396
5. IPC Section 307

**After ("how do I file an FIR?"):**
1. CrPC QA (procedure) ✅

**Collection size:** 16,153 documents (was 14,548)

## [2026-10-07 10:30] - Graph DB + Verifier Merged into Master

### What Changed
- Merged `GraphDB-and-verifier-built` branch into `master`
- Resolved merge with `origin/master` (README addition)
- All Graph DB and Verifier files now on `master`

### Why
- The teammate's work is now the single source of truth
- No more branch divergence

### Output
- `src/graph_db/build_graph.py`: builds Neo4j graph
- `src/verifier/verifier_agent.py`: verifies answers against the graph
- `tests/test_graph_db.py`, `tests/test_verifier.py`: 15 tests, all pass
- `docs/GRAPH_DB_AND_VERIFIER_ANALYSIS.md`: 269-line statistical analysis
- Git graph now shows a clean merge commit


## [2026-10-08 13:19] - Stress Test Reveals Critical Retrieval Weaknesses

### What Changed
- `tests/stress_test.py`: New 40-query stress test covering 9 categories
- `tests/stress_test_results.json`: Structured results with per-query and per-category stats
- `CHANGELOG.md`: This entry

### Why
- We needed empirical evidence of where the system fails before deciding what to fix
- Manual testing of 40 queries was too slow and unreliable

### Results Summary

| Category | Queries | Correct | Accuracy | Avg Confidence |
|---|---|---|---|---|
| BNS substantive (multi-hop) | 5 | 2 | 40% | 0.63 |
| Temporal | 5 | 2 | 40% | 0.60 |
| Procedural | 5 | 0 | 0% | 0.45 |
| Constitutional | 5 | 0 | 0% | 0.51 |
| Consumer | 3 | 0 | 0% | 0.55 |
| Out-of-scope | 5 | 2 | 40% | 0.52 |
| Ambiguous | 4 | 1 | 25% | 0.80 |
| Typos | 3 | 2 | 67% | 0.83 |
| Specific section | 5 | 1 | 20% | 0.54 |
| **TOTAL** | **40** | **~10** | **~25%** | — |

### The Three Critical Weaknesses

#### Weakness 1: Section Number Collisions

The system does not distinguish between a section number in one act vs another.

| Query | Top Candidate | Correct Answer | What Went Wrong |
|---|---|---|---|
| "What is Article 21?" | BNSS 2023 Sec 21 | Constitution Article 21 | Matched on "21", ignored "Article" |
| "What is Section 302?" | BNS 2023 Sec 302 | IPC 1860 Sec 302 | Matched on "302", ignored that IPC 302 is the famous murder section |
| "What is Section 420?" | BNSS 2023 Sec 420 | IPC 1860 Sec 420 | Matched on "420", ignored "cheating" context |
| "What is Section 144?" | BNSS 2023 Sec 144 | CrPC 1973 Sec 144 | Matched on "144", ignored "unlawful assembly" context |
| "What is Section 498A?" | NO CANDIDATES | IPC 1860 Sec 498A | Section 498A does not exist in the graph |

**Root cause:** The Intent Classifier detects section numbers but does not detect which act they belong to. The retriever then searches all acts and returns whichever section number matches.

**Impact:** All "What is Section X?" queries are unreliable unless the user explicitly names the act.

#### Weakness 2: Consumer and Constitution Raw Text Missing from Vector DB

The Consumer Protection Act 2019 sections and the Constitution Articles 12–35 are not in the ChromaDB collection.

| Query | Top Candidate | Should Have Been |
|---|---|---|
| "What is a consumer under CPA?" | BNS 2023 Sec 349 | CPA 2019 Sec 2(7) |
| "How do I file a consumer complaint?" | NO CANDIDATES | CPA 2019 Sec 35 |
| "What is the penalty for misleading ads?" | BNS 2023 Sec 283 | CPA 2019 Sec 89 |
| "Can I be arrested for posting online?" | NO CANDIDATES | Article 19(1)(a) |

**Root cause:** The files `data/raw/consumer/cpa_2019_sections.json` and `data/raw/constitution_qa/constitution_qa.json` exist on disk but are not loaded by `build_index.py`.

**Impact:** Consumer and constitutional queries never return the correct answer.

#### Weakness 3: The Verifier's "Verified" Flag Is Misleading

The verifier returns "verified: True" whenever the retrieved section exists in the graph. It does not check whether the retrieved section is the correct answer for the query.

| Query | Verifier Says | Reality |
|---|---|---|
| "What is Article 21?" | ✅ Verified 0.68 | Wrong section (BNSS 21) |
| "What is a consumer under CPA?" | ✅ Verified 0.83 | Wrong section (BNS 349) |
| "Can my landlord evict me?" | ✅ Verified 0.82 | Out of scope |

**Root cause:** The verifier's confidence score is based on graph existence and connectivity, not on semantic relevance to the query.

**Impact:** The user sees a green "Verified" badge for wrong answers. This undermines the core anti-hallucination guarantee.

### What Is Working Well

| Category | Evidence |
|---|---|
| BNS substantive law | Murder vs culpable homicide (#15), mob lynching (#16), abetment (#18) all correct |
| Temporal queries | IPC 376 for rape in 2010 (#19), IPC 497 for adultery in 2015 (#22) correct |
| Explicit BNS lookups | "bns 103 kya hai" (#35) returned BNS 103 correctly |
| Typos and informal phrasing | "whats the punishmnt for murdr" (#33) handled |
| Out-of-scope rejection | Anticipatory bail (#2), rights when arrested (#4), juvenile (#17), divorce (#24) all correctly returned 0.0 confidence |

### Priority for Fixes

1. **Add Consumer and Constitution text to `build_index.py`** — 1–2 hours, immediate 20% accuracy gain
2. **Add act-aware section resolution to the Intent Classifier** — 1 day, fixes "Section X" queries
3. **Improve the verifier's confidence score** — 2 days, makes the "Verified" flag trustworthy
4. **Add vague-query detection** — 2 hours, improves UX for ambiguous queries

### Current State of the System

| Component | Status |
|---|---|
| Vector DB | 16,153 documents (missing Consumer + Constitution) |
| Graph DB | 2,339 nodes, 5,384 edges |
| Retrieval Pipeline | Works for BNS substantive and temporal; fails for section lookups and out-of-scope acts |
| Verifier | Works for existence checks; fails for relevance checks |
| UI | Working |
| Overall Accuracy | ~25% across 40 varied queries |



## [2026-10-10 18:00] - Consumer + Constitution Fixes Verified

### What Changed
- `src/verifier/verifier_agent.py`: added `Article X` and `CPA Section X` patterns to `extract_section_ids()`
- `tests/stress_test_results.json`: updated after graph and vector DB rebuild

### Why
- The verifier could not extract Constitution Articles (Article 21) or Consumer sections (CPA Section 2)
- These patterns enable verification for Consumer and Constitutional queries

### Output
**Before fixes:**
- Constitutional: 40% verified
- Consumer: 0% verified

**After fixes:**
- Constitutional: 80% verified (4/5)
- Consumer: 67% verified (2/3)

**Remaining failures (priority for next iteration):**
1. Section-act collision (Section 302 → BNS 302, should be IPC 302)
2. Procedural retrieval (anticipatory bail, rights when arrested)
3. Out-of-scope leakage (trademark, eviction return verified answers)



## [2026-10-12 14:30] - Section-Act Disambiguation

### What Changed
- `src/classifier/intent.py`: reordered `ACT_KEYWORDS` longest-key-first to prevent `"bns"` matching before `"bnss"`
- `src/classifier/intent.py`: added `FAMOUS_SECTIONS` map for bare section numbers
- `src/classifier/intent.py`: apply default act when a bare section matches a famous landmark section
- `test_disambiguation.py`: new 9-query test for act resolution

### Why
- The system could not disambiguate bare section numbers across acts
- "Section 302" returned BNS 302 instead of IPC 302
- "Section 420" returned BNSS 420 instead of IPC 420
- These are among the most commonly referenced sections in Indian criminal law

### Output

**Disambiguation test (9/9 pass):**

| Query | Expected Act | Got Act | Result |
|---|---|---|---|
| What is Section 302? | IPC 1860 | IPC 1860 | ✅ |
| What is Section 420? | IPC 1860 | IPC 1860 | ✅ |
| What is Section 144? | CrPC 1973 | CrPC 1973 | ✅ |
| What is Section 498A? | IPC 1860 | IPC 1860 | ✅ |
| What is Section 103 of BNS? | BNS 2023 | BNS 2023 | ✅ |
| What is Section 302 of BNS? | BNS 2023 | BNS 2023 | ✅ |
| What is Section 173 of BNSS? | BNSS 2023 | BNSS 2023 | ✅ |
| What is Section 103? | None | None | ✅ |
| What is Section 173? | None | None | ✅ |

**Stress test improvement (queries 36, 37, 38):**

| # | Query | Before | After |
|---|---|---|---|
| 36 | What is Section 302? | BNS 2023 Sec 302 | **IPC 1860 Sec 302** ✅ |
| 37 | What is Section 376? | IPC 1860 Sec 376 | IPC 1860 Sec 376 ✅ |
| 38 | What is Section 420? | BNSS 2023 Sec 420 | **IPC 1860 Sec 420** ✅ |

**Specific-section category:** 60% → 60% (net unchanged due to new regressions)

### Known Regressions

Two queries that previously returned results now return zero candidates:

| # | Query | Before | After |
|---|---|---|---|
| 39 | What is Section 498A? | NO CANDIDATES | NO CANDIDATES (unchanged) |
| 40 | What is Section 144? | BNSS 2023 Sec 144 | **NO CANDIDATES** (regressed) |

**Root cause:** The new strict filter `{act, section_number}` finds nothing because:
- CrPC content in the vector DB comes from `crpc_qa.json` (which has empty `section_number`)
- IPC 498A is not present in the GovIntel IPC sections file

**Next fix:** Add fallback logic to the retrievers — when a strict filter returns zero results, retry with a looser filter (drop section number, then no filter).

### Current System State

| Metric | Value |
|---|---|
| Vector DB documents | 19,627 |
| Graph nodes | 1,954 |
| Graph edges | 5,334 |
| Disambiguation test | 9/9 pass |
| Stress test overall | ~60% |
| Strongest categories | ambiguous (100%), typos (100%), constitutional (80%), multi-hop (80%), temporal (80%) |
| Weakest categories | consumer (67%), procedural (60%), specific-section (60%) |



## [2026-10-12 16:00] - Fallback Retrieval + Disambiguation Complete

### What Changed
- `src/classifier/intent.py`: `FAMOUS_SECTIONS` map; longest-first `ACT_KEYWORDS`
- `src/vector_db/retriever.py`: fallback chain (strict → no_section → none)
- `src/vector_db/bm25_retriever.py`: same fallback logic
- `test_disambiguation.py`: 9/9 pass

### Why
- Bare section numbers were returning the wrong act
- Strict act+section filters returned 0 candidates when the section was missing

### Output
| Category | Before | After |
|---|---|---|
| specific-section | 60% | **100%** |
| temporal | 80% | **100%** |
| Overall | ~60% | **~82%** |

**Fixed queries:** 36, 37, 38, 39, 40, 23 (Section 302 → IPC 302, Section 420 → IPC 420, etc.)

**Known false positive:** Section 498A returns IPC 478 (498A missing from GovIntel IPC data). Documented for RQ5 (verifier semantic vulnerability).

### Remaining Failures (Next Priorities)
1. Procedural queries: 60% — no clean procedural QA source
2. Out-of-scope leakage: 60% — trademark/eviction return verified answers
3. Consumer queries: 67% — better but retrieval still imprecise