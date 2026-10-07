"""
integration.py — Connects the Retrieval Pipeline to the Verifier Agent.

Flow:
  User Query
      ↓
  Retrieval Pipeline → top-5 candidates
      ↓
  Verifier Agent → confidence score
      ↓
  Decision:
      - confidence >= 0.5 → Verified answer
      - confidence < 0.5  → Soft warning (answer + low confidence flag)
"""

from dataclasses import dataclass, field

from src.pipeline import RetrievalPipeline
from src.verifier.verifier_agent import VerifierAgent


# ──────────────────────────────────────────────
# Section ID conversion
# ──────────────────────────────────────────────

ACT_PREFIX_MAP = {
    "BNS 2023": "BNS_2023",
    "BNSS 2023": "BNSS_2023",
    "BSA 2023": "BSA_2023",
    "IPC 1860": "IPC_1860",
    "CrPC 1973": "CrPC_1973",
    "IEA 1872": "IEA_1872",
}


def to_verifier_id(act: str, section_number: str) -> str:
    """Convert Vector DB metadata (act + section_number) to Verifier ID format.

    Example:
        act="BNS 2023", section_number="103" → "BNS_2023_SEC_103"
    """
    if not act or not section_number:
        return ""
    prefix = ACT_PREFIX_MAP.get(act, act.replace(" ", "_"))
    return f"{prefix}_SEC_{str(section_number).zfill(3)}"


# ──────────────────────────────────────────────
# Integrated result
# ──────────────────────────────────────────────

@dataclass
class IntegratedResult:
    query: str
    verified: bool
    confidence: float
    answer: str
    candidates: list = field(default_factory=list)
    verification_reason: str = ""
    warning: str = ""

    def to_dict(self):
        return {
            "query": self.query,
            "verified": self.verified,
            "confidence": round(self.confidence, 3),
            "answer": self.answer,
            "candidate_count": len(self.candidates),
            "top_candidates": [
                {
                    "act": c["metadata"].get("act", ""),
                    "section": c["metadata"].get("section_number", ""),
                    "source": c["metadata"].get("source", ""),
                }
                for c in self.candidates[:5]
            ],
            "verification_reason": self.verification_reason,
            "warning": self.warning,
        }


# ──────────────────────────────────────────────
# Integrated pipeline
# ──────────────────────────────────────────────

class IntegratedLegalAssistant:
    def __init__(self):
        print("Initializing Integrated Legal Assistant...")
        self.retrieval = RetrievalPipeline()
        self.verifier = VerifierAgent()
        print("Ready.\n")

    def close(self):
        self.verifier.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def ask(self, query: str, top_k: int = 5) -> IntegratedResult:
        """Run the full pipeline: retrieve → verify → decide."""
        # Step 1: Retrieve
        candidates, intent = self.retrieval.retrieve(query, top_k=top_k)

        if not candidates:
            return IntegratedResult(
            query=query,
            verified=False,
            confidence=0.0,
            answer="No relevant legal provisions found for this query.",
            candidates=[],
            verification_reason="Retrieval returned zero candidates.",
            warning=(
                "This query does not match any provision in the legal knowledge base. "
                "The section may not exist, or the query may be outside the project's scope."
            ),
        )

        # Step 2: Build a draft answer from top candidate
        top = candidates[0]
        act = top["metadata"].get("act", "")
        section = top["metadata"].get("section_number", "")
        text = top["text"]

        draft_answer = self._build_draft_answer(act, section, text)

        # Step 3: Verify
        verification = self.verifier.verify(query, draft_answer)

        # Step 4: Decide
        verified = verification.verified
        confidence = verification.confidence

        warning = ""
        if not verified:
            warning = (
                "Low confidence — this answer could not be fully verified against "
                "the legal knowledge graph. Please consult a qualified lawyer."
            )

        return IntegratedResult(
            query=query,
            verified=verified,
            confidence=confidence,
            answer=draft_answer,
            candidates=candidates,
            verification_reason=verification.reason,
            warning=warning,
        )

    @staticmethod
    def _build_draft_answer(act: str, section: str, text: str) -> str:
        """Compose a draft answer from the top retrieved candidate."""
        if act and section:
            header = f"Under Section {section} of {act}:\n"
        elif act:
            header = f"Under {act}:\n"
        else:
            header = ""
        return header + text


# ──────────────────────────────────────────────
# CLI test
# ──────────────────────────────────────────────

if __name__ == "__main__":
    test_queries = [
        "What is the punishment for murder?",
        "What does Section 103 of BNS say?",
        "What was the punishment for murder in 2010?",
        "How do I file an FIR?",
        "Can someone be arrested under BNS Section 999 for cyberbullying?",
    ]

    with IntegratedLegalAssistant() as assistant:
        for q in test_queries:
            result = assistant.ask(q)
            print("=" * 70)
            print(f"Query      : {q}")
            print(f"Verified   : {result.verified}")
            print(f"Confidence : {result.confidence:.3f}")
            print(f"Reason     : {result.verification_reason}")
            if result.warning:
                print(f"Warning    : {result.warning}")
            print(f"Answer     : {result.answer[:250]}...")
            print()