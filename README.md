# Unified Legal Assistant for India

An offline legal AI assistant designed for Indian law that prioritizes accuracy, traceability, and privacy.

## Why this project

Most legal chatbots treat law as plain text search. That creates three major problems:

- **Hallucinations:** fabricated sections or incorrect legal claims
- **No time awareness:** inability to answer law-as-of-date questions
- **Online dependency:** privacy risk and poor access in low-connectivity regions

This project addresses those gaps with a verifiable, temporal, domain-aware, and offline-first system.

## Core capabilities

1. **Graph-constrained verification**  
   Every answer must map to a valid legal reasoning path in a knowledge graph (IRAC-style structure), with real citations.

2. **Temporal law tracking**  
   Legal provisions are stored with effective dates, amendments, and repeals, enabling date-specific legal lookup.

3. **Domain-partitioned retrieval**  
   Separate retrieval routes for:
   - Supreme Court case law
   - Statutory and constitutional text
   - Penal law (IPC/BNS)

4. **Offline-first deployment**  
   Runs locally without cloud APIs so legal queries stay on-device.

## System flow

1. **Query classification** selects legal domain and temporal intent.
2. **Graph retrieval** fetches connected legal nodes from Neo4j.
3. **Path verification** validates that a complete reasoning chain exists.
4. **Response generation** uses a local quantized Llama model to produce plain-language output with citations.
5. **Temporal toggle** switches between current law and law as-of a selected date.

## Practical value

- **Trust:** users can trace answers back to cited sections and judgments.
- **Access:** provides fast legal guidance for people who cannot easily reach legal counsel.
- **Privacy:** sensitive legal questions remain local to the user’s device.

## Vision

Unified Legal Assistant aims to make legal information more dependable and accessible in India by combining legal structure, time-aware reasoning, and offline usability in one system.
