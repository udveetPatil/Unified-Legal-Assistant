"""
Intent Classifier for the query pipeline.
Extracts structured signals from a user query.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryIntent:
    raw_query: str
    domain: str = "criminal"           # criminal | constitutional | consumer
    complexity: str = "simple"          # simple | complex
    legal_type: str = "substantive"     # substantive | procedural | unclear
    act: Optional[str] = None           # BNS 2023 | BNSS 2023 | BSA 2023 | IPC 1860 | CrPC 1973
    section_number: Optional[str] = None
    question_type: Optional[str] = None  # definitional | scenario | consequence | elements | exceptions
    is_temporal: bool = False


# ----- Keyword maps -----
ACT_KEYWORDS = {
    "bns": "BNS 2023",
    "bharatiya nyaya sanhita": "BNS 2023",
    "bnss": "BNSS 2023",
    "bharatiya nagarik suraksha sanhita": "BNSS 2023",
    "bsa": "BSA 2023",
    "bharatiya sakshya adhiniyam": "BSA 2023",
    "ipc": "IPC 1860",
    "indian penal code": "IPC 1860",
    "crpc": "CrPC 1973",
    "code of criminal procedure": "CrPC 1973",
    "iea": "IEA 1872",
    "indian evidence act": "IEA 1872",
}

QUESTION_TYPE_KEYWORDS = {
    "punishment": "consequence",
    "penalty": "consequence",
    "sentence": "consequence",
    "what happens if": "consequence",
    "define": "definitional_section",
    "what is": "definitional_section",
    "meaning of": "definitional_section",
    "elements": "elements",
    "ingredients": "elements",
    "constitute": "elements",
    "exception": "exceptions",
    "defence": "exceptions",
    "defense": "exceptions",
}

TEMPORAL_KEYWORDS = [
    "before 2024", "old law", "prior to", "previously",
    "was the law", "used to be",
    "2010", "2015", "2020", "history", "changed",
]

COMPLEXITY_KEYWORDS = [
    "can i", "should i", "what if", "my friend", "my",
    "how do i", "is it legal", "am i", "scenario",
]

PROCEDURAL_KEYWORDS = [
    "procedure", "how to file", "how do i file", "file a case",
    "fir", "first information report", "arrest", "bail", "anticipatory bail",
    "trial", "court", "hearing", "summons", "warrant",
    "investigation", "charge sheet", "chargesheet",
    "evidence", "witness", "testimony", "cross-examination",
    "appeal", "revision", "review",
    "jurisdiction", "territorial jurisdiction",
    "complaint", "prosecution",
]

SUBSTANTIVE_KEYWORDS = [
    "punishment", "penalty", "sentence", "imprisonment", "fine",
    "what is", "define", "definition", "meaning",
    "offence", "offense", "crime",
    "murder", "theft", "robbery", "dacoity", "assault",
    "rape", "kidnapping", "cheating", "fraud",
    "section", "ingredients", "elements",
]


def classify(query: str) -> QueryIntent:
    """Classify a user query into structured intent."""
    intent = QueryIntent(raw_query=query)
    q_lower = query.lower()

    # ----- Domain detection -----
    if any(kw in q_lower for kw in ["fundamental right", "article", "constitution"]):
        intent.domain = "constitutional"
    elif any(kw in q_lower for kw in ["consumer", "product", "defective", "refund"]):
        intent.domain = "consumer"
    else:
        intent.domain = "criminal"

    # ----- Act detection -----
    for kw, act in ACT_KEYWORDS.items():
        if kw in q_lower:
            intent.act = act
            break

    # ----- Section number extraction -----
    section_match = re.search(r"section\s+(\d+[a-z]?)", q_lower)
    if section_match:
        intent.section_number = section_match.group(1)

    # ----- Question type detection -----
    for kw, qtype in QUESTION_TYPE_KEYWORDS.items():
        if kw in q_lower:
            intent.question_type = qtype
            break

    # ----- Temporal detection -----
    intent.is_temporal = any(kw in q_lower for kw in TEMPORAL_KEYWORDS)

    # ----- Complexity detection -----
    if any(kw in q_lower for kw in COMPLEXITY_KEYWORDS):
        intent.complexity = "complex"

    # ----- Legal type detection -----
    procedural_score = sum(1 for kw in PROCEDURAL_KEYWORDS if kw in q_lower)
    substantive_score = sum(1 for kw in SUBSTANTIVE_KEYWORDS if kw in q_lower)

    if procedural_score > substantive_score:
        intent.legal_type = "procedural"
    elif substantive_score > procedural_score:
        intent.legal_type = "substantive"
    else:
        intent.legal_type = "unclear"

    return intent


if __name__ == "__main__":
    test_queries = [
        "What is the punishment for murder?",
        "What does Section 103 of BNS say?",
        "How do I file an FIR?",
        "What are the grounds for anticipatory bail?",
        "What was the punishment for murder in 2010?",
        "My friend was arrested without a warrant. What are his rights?",
        "What is the procedure for a criminal trial?",
    ]
    for q in test_queries:
        intent = classify(q)
        print(f"\nQuery: {q}")
        print(f"  legal_type : {intent.legal_type}")
        print(f"  act        : {intent.act}")
        print(f"  section    : {intent.section_number}")
        print(f"  q_type     : {intent.question_type}")
        print(f"  temporal   : {intent.is_temporal}")
        print(f"  complexity : {intent.complexity}")