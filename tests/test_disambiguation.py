from src.classifier.intent import classify

tests = [
    ("What is Section 302?", "IPC 1860", "302"),
    ("What is Section 420?", "IPC 1860", "420"),
    ("What is Section 144?", "CrPC 1973", "144"),
    ("What is Section 498A?", "IPC 1860", "498a"),
    ("What is Section 103 of BNS?", "BNS 2023", "103"),
    ("What is Section 302 of BNS?", "BNS 2023", "302"),
    ("What is Section 173 of BNSS?", "BNSS 2023", "173"),
    ("What is Section 103?", None, "103"),
    ("What is Section 173?", None, "173"),
]

print(f"{'Query':<40}{'Expected':<15}{'Got':<15}{'Section':<10}{'Pass'}")
print("-" * 95)

for query, exp_act, exp_sec in tests:
    intent = classify(query)
    passed = intent.act == exp_act and intent.section_number == exp_sec
    print(f"{query:<40}{str(exp_act):<15}{str(intent.act):<15}{str(intent.section_number):<10}{'✅' if passed else '❌'}")