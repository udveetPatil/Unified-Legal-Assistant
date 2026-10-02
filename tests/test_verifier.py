"""
tests/test_verifier.py — Replicable unit and integration tests for VerifierAgent.
Tests entity extraction, path finding, temporal verification, and hallucination rejection.
"""

import pytest
from src.verifier.verifier_agent import VerifierAgent


@pytest.fixture(scope="module")
def verifier():
    """Shared VerifierAgent instance."""
    agent = VerifierAgent()
    yield agent
    agent.close()


def test_section_id_extraction():
    """Verify regex extraction of legal sections from natural language text."""
    text = (
        "Under Section 103 of BNS and Section 302 of the IPC, murder is defined. "
        "Also see Section 176 of BNSS and Section 120 of BSA."
    )
    extracted = VerifierAgent.extract_section_ids(text)
    
    # Should find normalized IDs for all 4 acts
    assert "BNS_2023_SEC_103" in extracted
    assert "IPC_1860_SEC_302" in extracted
    assert "BNSS_2023_SEC_176" in extracted
    assert "BSA_2023_SEC_120" in extracted


def test_temporal_transition_verification(verifier):
    """Verify valid transition from IPC to BNS for murder offense."""
    query = "What section in BNS corresponds to IPC 302 for murder?"
    answer = "Section 103 of BNS 2023 replaces Section 302 of the IPC for punishment of murder."
    
    result = verifier.verify(query, answer)
    
    assert result.verified is True
    assert result.confidence >= 0.70
    assert len(result.paths) >= 1
    assert "BNS_2023_SEC_103" in result.matched_sections
    assert "IPC_1860_SEC_302" in result.matched_sections
    
    # Verify temporal pair relationship was found in path
    has_temporal = any("IPC_TEMPORAL_PAIR" in p["relationships"] for p in result.paths)
    assert has_temporal is True


def test_cross_code_verification(verifier):
    """Verify procedure and evidence links across BNS, BNSS, and BSA."""
    query = "What are the procedural rules for rape trials?"
    answer = (
        "Under Section 64 of BNS, trial procedure is governed by Section 176 of BNSS "
        "and evidentiary presumption is under Section 120 of BSA."
    )
    
    result = verifier.verify(query, answer)
    
    assert result.verified is True
    assert result.confidence >= 0.75
    assert len(result.paths) >= 1
    
    rel_types = {rel for p in result.paths for rel in p["relationships"]}
    assert "CROSS_CODE_PROCEDURE" in rel_types or "CROSS_CODE_EVIDENCE" in rel_types


def test_property_offense_theft_verification(verifier):
    """Verify theft provision under BNS 303 maps to IPC 379."""
    query = "What is the punishment for theft under BNS and IPC?"
    answer = "Theft is defined under Section 303 of BNS 2023 corresponding to Section 379 of IPC 1860."
    
    result = verifier.verify(query, answer)
    
    assert result.verified is True
    assert result.confidence >= 0.70
    assert "BNS_2023_SEC_303" in result.matched_sections


def test_hallucination_rejection(verifier):
    """Verify nonexistent / fabricated legal section is rejected with zero confidence."""
    query = "Can someone be arrested under BNS Section 999 for cyberbullying?"
    answer = "Under Section 999 of BNS 2023, cyberbullying is punishable with 5 years imprisonment."
    
    result = verifier.verify(query, answer)
    
    assert result.verified is False
    assert result.confidence == 0.0
    assert len(result.matched_sections) == 0
    assert len(result.paths) == 0
    assert "exist" in result.reason.lower()


def test_empty_query_handling(verifier):
    """Verify empty text returns unverified result without crashing."""
    result = verifier.verify("", "")
    assert result.verified is False
    assert result.confidence == 0.0
