"""
stress_test.py — Run a batch of queries through the integrated pipeline
and print a structured report.

Run:  python stress_test.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integration import IntegratedLegalAssistant


# ──────────────────────────────────────────────
# Test queries with expected answers
# ──────────────────────────────────────────────
TEST_QUERIES = [
    # Category 1: Procedural
    ("procedural", "How do I file an FIR?", "CrPC 154 / BNSS 173"),
    ("procedural", "What are the grounds for anticipatory bail?", "CrPC 438 / BNSS 482"),
    ("procedural", "What is a zero FIR?", "BNSS 173"),
    ("procedural", "What are my rights when arrested?", "CrPC 50/50A"),
    ("procedural", "How long can police keep me in custody?", "CrPC 57 / BNSS 58"),

    # Category 2: Constitutional
    ("constitutional", "What is Article 21?", "Right to life"),
    ("constitutional", "What does the right to equality say?", "Article 14"),
    ("constitutional", "Can I be arrested for posting something online?", "Article 19(1)(a)"),
    ("constitutional", "What is the right against self-incrimination?", "Article 20(3)"),
    ("constitutional", "Is the death penalty constitutional?", "Case law"),

    # Category 3: Consumer
    ("consumer", "What is a consumer under the Consumer Protection Act?", "CPA 2(7)"),
    ("consumer", "How do I file a consumer complaint?", "CPA 2019"),
    ("consumer", "What is the penalty for misleading advertisements?", "CPA 89"),

    # Category 4: Multi-hop
    ("multi-hop", "If someone commits murder during a robbery, what sections apply?", "BNS 103 + BNS 309"),
    ("multi-hop", "What is the difference between murder and culpable homicide?", "BNS 101 vs 105"),
    ("multi-hop", "What happens if a mob kills someone because of their caste?", "BNS 103(2)"),
    ("multi-hop", "Can a 16-year-old be tried as an adult?", "Juvenile Justice Act"),
    ("multi-hop", "What is the punishment for abetment of murder?", "BNS 49 + BNS 103"),

    # Category 5: Temporal
    ("temporal", "What was the punishment for rape in 2010?", "IPC 376"),
    ("temporal", "What is the punishment for rape now?", "BNS 64"),
    ("temporal", "What changed from IPC 302 to BNS 103?", "Temporal mapping"),
    ("temporal", "Was adultery a crime in 2015?", "IPC 497"),
    ("temporal", "What replaced the Indian Evidence Act?", "BSA 2023"),

    # Category 6: Out of scope
    ("out-of-scope", "How do I file for divorce?", "Not in scope"),
    ("out-of-scope", "What is the tax rate for small businesses?", "Not in scope"),
    ("out-of-scope", "How do I register a trademark?", "Not in scope"),
    ("out-of-scope", "What is the punishment under Section 420?", "IPC 420"),
    ("out-of-scope", "Can my landlord evict me?", "Civil law"),

    # Category 7: Ambiguous
    ("ambiguous", "Is it illegal?", "Should ask for clarification"),
    ("ambiguous", "Punishment?", "Low confidence expected"),
    ("ambiguous", "murder", "Should return murder section"),
    ("ambiguous", "What is the law?", "Too vague"),

    # Category 8: Typos / informal
    ("typo", "whats the punishmnt for murdr", "Should handle typo"),
    ("typo", "i wanna know about theft laws", "Informal"),
    ("typo", "bns 103 kya hai", "Hindi-English mix"),

    # Category 9: Specific sections
    ("specific-section", "What is Section 302?", "IPC murder"),
    ("specific-section", "What is Section 376?", "IPC rape"),
    ("specific-section", "What is Section 420?", "IPC cheating"),
    ("specific-section", "What is Section 498A?", "IPC cruelty"),
    ("specific-section", "What is Section 144?", "CrPC unlawful assembly"),
]


def main():
    print("=" * 100)
    print("STRESS TEST — Unified Legal Assistant")
    print("=" * 100)

    with IntegratedLegalAssistant() as assistant:
        results = []
        for i, (category, query, expected) in enumerate(TEST_QUERIES, 1):
            print(f"\n[{i}/{len(TEST_QUERIES)}] ({category}) {query}")

            try:
                result = assistant.ask(query)
                top = result.candidates[0] if result.candidates else None

                if top:
                    meta = top.get("metadata", {})
                    top_str = f"{meta.get('act', '?')} Sec {meta.get('section_number', '?')} ({meta.get('source', '?')})"
                else:
                    top_str = "NO CANDIDATES"

                print(f"  Top       : {top_str}")
                print(f"  Verified  : {result.verified}")
                print(f"  Confidence: {result.confidence:.3f}")
                print(f"  Expected  : {expected}")
                if result.warning:
                    print(f"  Warning   : {result.warning[:80]}...")

                results.append({
                    "num": i,
                    "category": category,
                    "query": query,
                    "top": top_str,
                    "verified": result.verified,
                    "confidence": result.confidence,
                    "expected": expected,
                })

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "num": i,
                    "category": category,
                    "query": query,
                    "top": f"ERROR: {e}",
                    "verified": False,
                    "confidence": 0.0,
                    "expected": expected,
                })

    # ──────────────────────────────────────────────
    # Summary table
    # ──────────────────────────────────────────────
    print("\n\n" + "=" * 100)
    print("SUMMARY TABLE")
    print("=" * 100)
    print(f"{'#':<4}{'Category':<18}{'Conf':<8}{'Verified':<10}{'Top Candidate':<40}{'Query'}")
    print("-" * 100)

    for r in results:
        print(
            f"{r['num']:<4}"
            f"{r['category']:<18}"
            f"{r['confidence']:<8.3f}"
            f"{str(r['verified']):<10}"
            f"{r['top'][:38]:<40}"
            f"{r['query'][:40]}"
        )

    # ──────────────────────────────────────────────
    # Category-level stats
    # ──────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("CATEGORY STATS")
    print("=" * 100)

    from collections import defaultdict
    stats = defaultdict(lambda: {"total": 0, "verified": 0, "conf_sum": 0.0})

    for r in results:
        s = stats[r["category"]]
        s["total"] += 1
        if r["verified"]:
            s["verified"] += 1
        s["conf_sum"] += r["confidence"]

    print(f"{'Category':<20}{'Total':<8}{'Verified':<10}{'Verify %':<12}{'Avg Conf'}")
    print("-" * 100)
    for cat, s in sorted(stats.items()):
        pct = 100 * s["verified"] / s["total"]
        avg = s["conf_sum"] / s["total"]
        print(f"{cat:<20}{s['total']:<8}{s['verified']:<10}{pct:<12.1f}{avg:.3f}")

    # Save results to file
    import json
    from datetime import datetime
    out_path = Path("tests/stress_test_results.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "category_stats": {k: dict(v) for k, v in stats.items()},
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()