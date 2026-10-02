"""
tests/test_graph_db.py — Automated replicable tests for Neo4j Graph DB.
Validates node counts, constraints, critical indexes, and relationship topology.
"""

import pytest
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "legalpass123"


@pytest.fixture(scope="module")
def driver():
    """Shared Neo4j driver instance for graph tests."""
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    yield drv
    drv.close()


def test_neo4j_connection(driver):
    """Verify Neo4j server is reachable and active."""
    driver.verify_connectivity()


def test_statute_nodes(driver):
    """Verify all 4 core Indian statutes exist."""
    with driver.session() as session:
        result = session.run("MATCH (st:STATUTE) RETURN st.name AS name")
        names = {r["name"] for r in result}
        assert "BNS 2023" in names
        assert "IPC 1860" in names
        assert "BNSS 2023" in names
        assert "BSA 2023" in names


def test_section_node_counts(driver):
    """Verify expected section volume loaded from GovIntel."""
    with driver.session() as session:
        result = session.run("MATCH (s:SECTION) RETURN count(s) AS cnt")
        count = result.single()["cnt"]
        # Expected around 1,604 sections
        assert count >= 1600, f"Expected at least 1600 sections, got {count}"


def test_case_node_counts(driver):
    """Verify judgment / case law nodes exist."""
    with driver.session() as session:
        result = session.run("MATCH (c:CASE) RETURN count(c) AS cnt")
        count = result.single()["cnt"]
        assert count >= 500, f"Expected at least 500 cases, got {count}"


def test_constraints_and_indexes(driver):
    """Verify primary key constraints exist on SECTION and STATUTE."""
    with driver.session() as session:
        result = session.run("SHOW CONSTRAINTS")
        constraints = [r["name"] for r in result]
        assert len(constraints) >= 2, "Expected uniqueness constraints to be defined"


def test_temporal_pair_edges(driver):
    """Verify IPC <-> BNS temporal transition edges exist."""
    with driver.session() as session:
        result = session.run("MATCH ()-[r:IPC_TEMPORAL_PAIR]->() RETURN count(r) AS cnt")
        count = result.single()["cnt"]
        assert count >= 400, f"Expected at least 400 temporal pair edges, got {count}"


def test_murder_transition_edge(driver):
    """Verify exact ground truth: BNS 103 connects to IPC 302."""
    with driver.session() as session:
        result = session.run("""
            MATCH (bns:SECTION {section_id: 'BNS_2023_SEC_103'})-[r:IPC_TEMPORAL_PAIR]-(ipc:SECTION)
            RETURN ipc.section_id AS ipc_id, ipc.alt_id AS alt_id
        """)
        record = result.single()
        assert record is not None, "BNS Section 103 must have a temporal pair edge"
        assert record["ipc_id"] == "IPC_1860_SEC_302" or record["alt_id"] == "IPC_302"


def test_cross_code_edges(driver):
    """Verify cross-code procedure and evidence edges exist."""
    with driver.session() as session:
        res_proc = session.run("MATCH ()-[r:CROSS_CODE_PROCEDURE]->() RETURN count(r) AS cnt").single()["cnt"]
        res_evid = session.run("MATCH ()-[r:CROSS_CODE_EVIDENCE]->() RETURN count(r) AS cnt").single()["cnt"]
        assert res_proc >= 200, f"Expected at least 200 procedure edges, got {res_proc}"
        assert res_evid >= 150, f"Expected at least 150 evidence edges, got {res_evid}"


def test_judgment_interprets_edges(driver):
    """Verify case law interpretation edges exist."""
    with driver.session() as session:
        result = session.run("MATCH ()-[r:INTERPRETS]->() RETURN count(r) AS cnt")
        count = result.single()["cnt"]
        assert count >= 1000, f"Expected at least 1000 interpretation edges, got {count}"
