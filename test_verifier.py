"""
test_verifier.py — Quick standalone test runner for Graph DB & Verifier Agent.
Run with: python test_verifier.py
"""

from src.verifier.verifier_agent import VerifierAgent
import json

def main():
    print("=" * 60)
    print("Unified Legal Assistant - Verifier Agent Test Runner")
    print("=" * 60)
    
    with VerifierAgent() as agent:
        # 1. Print graph statistics
        stats = agent.graph_stats()
        print("\n[1] Neo4j Graph Database Topology:")
        for label, count in sorted(stats.items()):
            print(f"    {label:<25}: {count}")

        # 2. Replicable test query suite
        suite = [
            (
                "Murder Transition (BNS 103 <-> IPC 302)",
                "What is the punishment for murder under BNS?",
                "Under Section 103 of BNS 2023, which replaces Section 302 of the IPC, murder is punishable with death or life imprisonment.",
                True
            ),
            (
                "Cross-Code Procedure & Evidence (Rape: BNS 64 -> BNSS 176 + BSA 120)",
                "What procedure and evidence rules apply to rape trials under BNSS and BSA?",
                "For offences under Section 64 of BNS, trial procedure is governed by Section 176 of BNSS and presumption of consent is under Section 120 of BSA.",
                True
            ),
            (
                "Property Offense (Theft: BNS 303 <-> IPC 379)",
                "What is the theft provision under BNS?",
                "Theft is punishable under Section 303 of BNS, corresponding to Section 379 of IPC.",
                True
            ),
            (
                "Hallucination Test (Fabricated Section 999)",
                "Is trolling punishable under BNS 999?",
                "Under Section 999 of BNS, online harassment carries a 7 year sentence.",
                False
            ),
        ]

        print("\n[2] Executing Verification Test Suite:")
        passed = 0
        for name, q, a, expected_verified in suite:
            print(f"\n--- {name} ---")
            res = agent.verify(q, a)
            success = (res.verified == expected_verified)
            tag = "[PASS]" if success else "[FAIL]"
            if success:
                passed += 1
            print(f"Status      : {tag} (Verified={res.verified}, Expected={expected_verified})")
            print(f"Confidence  : {res.confidence:.2f}")
            print(f"Paths Found : {len(res.paths)}")
            for p in res.paths[:2]:
                print(f"   -> {' -> '.join(p['nodes'])} [{', '.join(p['relationships'])}]")
            print(f"Reason      : {res.reason}")

        print("\n" + "=" * 60)
        print(f"Result: {passed}/{len(suite)} tests passed.")
        print("=" * 60)

if __name__ == "__main__":
    main()
