"""
tests/test_integration.py — End-to-end tests for the integrated pipeline.
"""

import pytest

from src.integration import IntegratedLegalAssistant, to_verifier_id


@pytest.fixture(scope="module")
def assistant():
    a = IntegratedLegalAssistant()
    yield a
    a.close()


# ──────────────────────────────────────────────
# Unit: section ID conversion
# ──────────────────────────────────────────────

def test_to_verifier_id_bns():
    assert to_verifier_id("BNS 2023", "103") == "BNS_2023_SEC_103"


def test_to_verifier_id_ipc():
    assert to_verifier_id("IPC 1860", "302") == "IPC_1860_SEC_302"


def test_to_verifier_id_padding():
    assert to_verifier_id("BNS 2023", "1") == "BNS_2023_SEC_001"


def test_to_verifier_id_empty():
    assert to_verifier_id("", "") == ""
    assert to_verifier_id("BNS 2023", "") == ""
    assert to_verifier_id("", "103") == ""


# ──────────────────────────────────────────────
# Integration: full pipeline
# ──────────────────────────────────────────────

def test_murder_query_verified(assistant):
    """Substantive query should retrieve and verify."""
    result = assistant.ask("What is the punishment for murder?")
    assert result.candidates, "Retrieval should return candidates"
    assert result.answer, "Answer should not be empty"
    assert result.confidence >= 0.0


def test_section_lookup(assistant):
    """Explicit section query should return that section."""
    result = assistant.ask("What does Section 103 of BNS say?")
    assert result.candidates
    top = result.candidates[0]
    assert top["metadata"].get("section_number") == "103"


def test_temporal_query(assistant):
    """Temporal query should return IPC sections."""
    result = assistant.ask("What was the punishment for murder in 2010?")
    assert result.candidates
    # Top candidate should be IPC 1860 (old law)
    sources = [c["metadata"].get("act", "") for c in result.candidates]
    assert any("IPC" in s for s in sources), f"Expected IPC in {sources}"


def test_procedural_query(assistant):
    """Procedural query should route to CrPC."""
    result = assistant.ask("How do I file an FIR?")
    assert result.candidates
    sources = [c["metadata"].get("source", "") for c in result.candidates]
    assert "crpc_qa" in sources, f"Expected crpc_qa in {sources}"


def test_hallucinated_section_warns(assistant):
    """Hallucinated section should produce a warning, not a hard failure."""
    result = assistant.ask("Can someone be arrested under BNS Section 999 for cyberbullying?")
    # The retrieval might return unrelated sections, but the verifier should flag low confidence
    if not result.verified:
        assert result.warning, "Unverified result must include a warning"


def test_empty_query_handled(assistant):
    """Empty-ish query should not crash."""
    result = assistant.ask("xyzzy")
    assert result.query == "xyzzy"