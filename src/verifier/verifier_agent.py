"""
verifier_agent.py — Graph-based legal answer verifier.
Queries Neo4j to validate that an LLM answer is grounded in the legal knowledge graph.
If a valid path exists between the query entities and cited law, the answer is verified.
"""

from neo4j import GraphDatabase
from typing import Optional
import re
import json


# --- Neo4j connection (same as build_graph) ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "legalpass123"


class VerificationResult:
    """Holds the outcome of a graph verification check."""

    def __init__(self, verified: bool, confidence: float, paths: list,
                 matched_sections: list, matched_cases: list, reason: str):
        self.verified = verified
        self.confidence = confidence
        self.paths = paths
        self.matched_sections = matched_sections
        self.matched_cases = matched_cases
        self.reason = reason

    def to_dict(self):
        return {
            "verified": self.verified,
            "confidence": round(self.confidence, 3),
            "paths_found": len(self.paths),
            "paths": self.paths[:5],  # cap to 5 for readability
            "matched_sections": self.matched_sections,
            "matched_cases": self.matched_cases,
            "reason": self.reason,
        }

    def __repr__(self):
        status = "[VERIFIED]" if self.verified else "[UNVERIFIED]"
        return f"{status} (confidence={self.confidence:.2f}, paths={len(self.paths)})"


class VerifierAgent:
    """Verifies legal answers by checking paths in the Neo4j knowledge graph."""

    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASS):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ──────────────────────────────────────────────
    # Section extraction from text
    # ──────────────────────────────────────────────

    @staticmethod
    def extract_section_ids(text: str) -> list[str]:
        """Extract section IDs like 'BNS_2023_SEC_103', 'IPC_1860_SEC_302' from text."""
        ids = []
        # Direct ID references
        ids.extend(re.findall(r'[A-Z]+_\d{4}_SEC_\d+[A-Z]?', text))

        # Natural language: "Section 302 of IPC" / "BNS Section 103"
        patterns = [
            (r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)\s*(?:of\s+)?(?:the\s+)?(?:IPC|Indian Penal Code)', 'IPC_1860_SEC_'),
            (r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)\s*(?:of\s+)?(?:the\s+)?(?:BNS|Bharatiya Nyaya Sanhita)', 'BNS_2023_SEC_'),
            (r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)\s*(?:of\s+)?(?:the\s+)?(?:BNSS|Bharatiya Nagarik Suraksha Sanhita)', 'BNSS_2023_SEC_'),
            (r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)\s*(?:of\s+)?(?:the\s+)?(?:BSA|Bharatiya Sakshya Adhiniyam)', 'BSA_2023_SEC_'),
            (r'(?:IPC|Indian Penal Code)\s*(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)', 'IPC_1860_SEC_'),
            (r'(?:BNS|Bharatiya Nyaya Sanhita)\s*(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)', 'BNS_2023_SEC_'),
        ]
        for pattern, prefix in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sec_num = match.group(1).zfill(3)
                ids.append(f"{prefix}{sec_num}")

        return list(set(ids))

    # ──────────────────────────────────────────────
    # Core graph queries
    # ──────────────────────────────────────────────

    def find_section(self, tx, section_id: str) -> Optional[dict]:
        """Check if a section exists in the graph."""
        result = tx.run("""
            MATCH (s:SECTION) WHERE s.section_id = $sid OR s.alt_id = $sid
            RETURN s.section_id AS id, s.title AS title, s.act AS act
            LIMIT 1
        """, sid=section_id)
        record = result.single()
        return dict(record) if record else None

    def find_path_between_sections(self, tx, src_id: str, tgt_id: str, max_hops: int = 4) -> list:
        """Find shortest path between two sections (any relationship)."""
        result = tx.run(f"""
            MATCH (a:SECTION) WHERE a.section_id = $src OR a.alt_id = $src
            MATCH (b:SECTION) WHERE b.section_id = $tgt OR b.alt_id = $tgt
            MATCH path = shortestPath((a)-[*1..{max_hops}]-(b))
            RETURN [n IN nodes(path) | coalesce(n.section_id, n.name, labels(n)[0])] AS node_ids,
                   [r IN relationships(path) | type(r)] AS rel_types
            LIMIT 3
        """, src=src_id, tgt=tgt_id)
        return [{"nodes": r["node_ids"], "relationships": r["rel_types"]} for r in result]

    def find_temporal_pair(self, tx, section_id: str) -> list[dict]:
        """Find IPC<->BNS temporal pairs for a section."""
        result = tx.run("""
            MATCH (a:SECTION) WHERE a.section_id = $sid OR a.alt_id = $sid
            MATCH (a)-[:IPC_TEMPORAL_PAIR]-(b:SECTION)
            RETURN b.section_id AS paired_id, b.title AS title, b.act AS act
        """, sid=section_id)
        return [dict(r) for r in result]

    def find_cross_code_links(self, tx, section_id: str) -> list[dict]:
        """Find cross-code procedure/evidence links for a section."""
        result = tx.run("""
            MATCH (a:SECTION) WHERE a.section_id = $sid OR a.alt_id = $sid
            MATCH (a)-[r:CROSS_CODE_PROCEDURE|CROSS_CODE_EVIDENCE]-(b:SECTION)
            RETURN b.section_id AS linked_id, b.title AS title, type(r) AS rel_type, r.reason AS reason
        """, sid=section_id)
        return [dict(r) for r in result]

    def find_interpreting_cases(self, tx, section_id: str) -> list[dict]:
        """Find cases that interpret a given section."""
        result = tx.run("""
            MATCH (s:SECTION) WHERE s.section_id = $sid OR s.alt_id = $sid
            MATCH (c:CASE)-[r:INTERPRETS]->(s)
            RETURN coalesce(c.case_id, c.file_id) AS case_id, coalesce(c.name, c.case_id) AS case_name, c.court AS court, r.weight AS weight
            ORDER BY r.weight DESC
            LIMIT 5
        """, sid=section_id)
        return [dict(r) for r in result]

    def find_section_neighborhood(self, tx, section_id: str) -> dict:
        """Get full neighborhood of a section: temporal pairs, cross-code, references."""
        result = tx.run("""
            MATCH (s:SECTION) WHERE s.section_id = $sid OR s.alt_id = $sid
            OPTIONAL MATCH (s)-[r]->(t:SECTION)
            RETURN s.section_id AS id, s.title AS title, s.act AS act,
                   collect(DISTINCT {target: t.section_id, rel: type(r)}) AS outgoing
            LIMIT 1
        """, sid=section_id)
        record = result.single()
        if not record:
            return {}
        return {
            "id": record["id"], "title": record["title"], "act": record["act"],
            "outgoing": [e for e in record["outgoing"] if e["target"] is not None],
        }

    def check_section_validity(self, tx, section_id: str) -> dict:
        """Check if a section is valid (exists and is connected in the graph)."""
        result = tx.run("""
            MATCH (s:SECTION) WHERE s.section_id = $sid OR s.alt_id = $sid
            OPTIONAL MATCH (s)-[r]-(other)
            RETURN s.section_id AS id, s.title AS title, s.act AS act,
                   count(r) AS connection_count
            LIMIT 1
        """, sid=section_id)
        record = result.single()
        if not record:
            return {"exists": False, "section_id": section_id}
        return {
            "exists": True, "section_id": record["id"],
            "title": record["title"], "act": record["act"],
            "connections": record["connection_count"],
        }

    # ──────────────────────────────────────────────
    # Main verification logic
    # ──────────────────────────────────────────────

    def verify(self, query: str, answer: str, cited_sections: list[str] = None) -> VerificationResult:
        """
        Verify a legal answer against the knowledge graph.

        Strategy:
        1. Extract section IDs from query + answer
        2. Check each section exists in graph
        3. Check paths between mentioned sections
        4. Check for temporal pairs (IPC<->BNS consistency)
        5. Check for interpreting case law & cross-code links
        6. Score overall confidence
        """
        all_text = f"{query} {answer}"
        if cited_sections:
            all_text += " " + " ".join(cited_sections)

        section_ids = cited_sections if cited_sections else self.extract_section_ids(all_text)

        if not section_ids:
            return VerificationResult(
                verified=False, confidence=0.0, paths=[], matched_sections=[],
                matched_cases=[], reason="No legal sections found in query or answer."
            )

        matched_sections = []
        unmatched = []
        all_paths = []
        all_cases = []
        scores = []

        with self.driver.session() as session:
            # Step 1: Verify each section exists in the graph
            for sid in section_ids:
                validity = session.execute_read(self.check_section_validity, sid)
                if validity.get("exists"):
                    matched_sections.append(validity)
                    # Grounded base score + connection boost
                    conn_score = min(validity["connections"] / 5.0, 1.0)
                    scores.append(0.5 + 0.3 * conn_score)
                else:
                    unmatched.append(sid)

            if not matched_sections:
                return VerificationResult(
                    verified=False, confidence=0.0, paths=[], matched_sections=[],
                    matched_cases=[], reason=f"None of the cited sections exist in graph: {unmatched}"
                )

            matched_ids = [s["section_id"] for s in matched_sections]

            # Step 2: Check paths between pairs of sections
            for i in range(len(matched_ids)):
                for j in range(i + 1, len(matched_ids)):
                    paths = session.execute_read(
                        self.find_path_between_sections, matched_ids[i], matched_ids[j]
                    )
                    if paths:
                        all_paths.extend(paths)
                        scores.append(0.9)

            # Step 3: Check temporal pairs (IPC<->BNS correspondence)
            for sid in matched_ids:
                pairs = session.execute_read(self.find_temporal_pair, sid)
                if pairs:
                    scores.append(0.85)
                    for p in pairs:
                        all_paths.append({
                            "nodes": [sid, p["paired_id"]],
                            "relationships": ["IPC_TEMPORAL_PAIR"],
                        })

            # Step 4: Check cross-code links
            for sid in matched_ids:
                cross = session.execute_read(self.find_cross_code_links, sid)
                if cross:
                    scores.append(0.8)
                    for c in cross:
                        all_paths.append({
                            "nodes": [sid, c["linked_id"]],
                            "relationships": [c["rel_type"]],
                            "reason": c.get("reason", ""),
                        })

            # Step 5: Find interpreting case law
            for sid in matched_ids:
                cases = session.execute_read(self.find_interpreting_cases, sid)
                all_cases.extend(cases)
                if cases:
                    scores.append(0.85)

        # Compute final confidence
        if not scores:
            confidence = 0.2 if matched_sections else 0.0
        else:
            confidence = sum(scores) / len(scores)

        # Penalize for unmatched sections
        if unmatched:
            penalty = len(unmatched) / (len(matched_sections) + len(unmatched))
            confidence *= (1 - penalty * 0.5)

        verified = confidence >= 0.5
        reason = self._build_reason(matched_sections, unmatched, all_paths, all_cases, confidence)

        return VerificationResult(
            verified=verified,
            confidence=min(confidence, 1.0),
            paths=all_paths,
            matched_sections=[s["section_id"] for s in matched_sections],
            matched_cases=[c["case_id"] for c in all_cases[:5]],
            reason=reason,
        )

    def _build_reason(self, matched, unmatched, paths, cases, confidence):
        """Build a human-readable verification reason string."""
        parts = []
        if matched:
            parts.append(f"Found {len(matched)} sections in graph.")
        if unmatched:
            parts.append(f"{len(unmatched)} sections not found: {', '.join(unmatched[:3])}.")
        if paths:
            parts.append(f"{len(paths)} connecting paths found between cited sections.")
        if cases:
            parts.append(f"{len(cases)} interpreting judgments found.")
        if confidence < 0.5:
            parts.append("Insufficient evidence to verify the legal claim.")
        return " ".join(parts) if parts else "No verification data available."

    # ──────────────────────────────────────────────
    # Utility: neighborhood lookup for the LLM
    # ──────────────────────────────────────────────

    def get_context_for_section(self, section_id: str) -> dict:
        """Get rich context for a section: neighbors, cases, temporal pairs."""
        with self.driver.session() as session:
            neighborhood = session.execute_read(self.find_section_neighborhood, section_id)
            cases = session.execute_read(self.find_interpreting_cases, section_id)
            temporal = session.execute_read(self.find_temporal_pair, section_id)
            cross = session.execute_read(self.find_cross_code_links, section_id)
        return {
            "section": neighborhood,
            "interpreting_cases": cases,
            "temporal_pairs": temporal,
            "cross_code_links": cross,
        }

    def graph_stats(self) -> dict:
        """Return basic stats about the graph for health checks."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt
                UNION ALL
                MATCH ()-[r]->() RETURN type(r) AS label, count(r) AS cnt
            """)
            stats = {r["label"]: r["cnt"] for r in result}
        return stats


# ──────────────────────────────────────────────
# CLI entry point for quick testing
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    with VerifierAgent() as agent:
        # Print graph stats
        stats = agent.graph_stats()
        print("Graph Stats:")
        for label, count in sorted(stats.items()):
            print(f"  {label}: {count}")

        # Quick verification test
        test_q = "What is the punishment for murder under BNS?"
        test_a = "Under Section 103 of BNS 2023, murder is punishable with death or imprisonment for life, and shall also be liable to fine."
        print(f"\nQuery: {test_q}")
        print(f"Answer: {test_a}")
        result = agent.verify(test_q, test_a)
        print(f"\n{result}")
        print(json.dumps(result.to_dict(), indent=2))
