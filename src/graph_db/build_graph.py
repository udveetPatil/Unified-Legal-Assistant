"""
build_graph.py — Loads InIRAC cases, GovIntel sections & edges into Neo4j.
Creates CASE, SECTION, STATUTE, RULE nodes and all relationship types.
"""

from neo4j import GraphDatabase
import json
from pathlib import Path
from rich.console import Console
from rich.progress import track

console = Console()

# --- Paths ---
BASE = Path(__file__).resolve().parent.parent.parent
INIRAC_DIR = BASE / "data" / "raw" / "inIRAC" / "data"
SECTIONS_DIR = BASE / "data" / "raw" / "govintel" / "sections"
GRAPH_DIR = BASE / "data" / "raw" / "govintel" / "graph"

# --- Neo4j connection ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "legalpass123"


def get_driver():
    """Create and return a Neo4j driver instance."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


# ──────────────────────────────────────────────
# Constraint & index setup (idempotent)
# ──────────────────────────────────────────────

def setup_constraints(tx):
    """Create uniqueness constraints and indexes for fast lookups."""
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SECTION) REQUIRE s.section_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (st:STATUTE) REQUIRE st.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:CASE) REQUIRE c.file_id IS UNIQUE")
    tx.run("CREATE INDEX IF NOT EXISTS FOR (s:SECTION) ON (s.alt_id)")
    tx.run("CREATE INDEX IF NOT EXISTS FOR (s:SECTION) ON (s.act, s.number)")
    tx.run("CREATE INDEX IF NOT EXISTS FOR (c:CASE) ON (c.case_id)")
    tx.run("CREATE INDEX IF NOT EXISTS FOR (c:CASE) ON (c.court)")


# ──────────────────────────────────────────────
# Node creators
# ──────────────────────────────────────────────

def create_statute_node(tx, name, year):
    """MERGE a STATUTE node (e.g. 'BNS 2023', 'IPC 1860')."""
    tx.run("""
        MERGE (st:STATUTE {name: $name})
        SET st.year = $year
    """, name=name, year=year)


def create_section_node(tx, sec):
    """MERGE a SECTION node from a GovIntel section dict."""
    sid = sec.get("section_id", "")
    if not sid:
        return
    alt_id = f"IPC_{sec['section_id_raw']}" if sec.get("section_id_raw") else None
    tx.run("""
        MERGE (s:SECTION {section_id: $sid})
        SET s.act       = $act,
            s.number    = $number,
            s.title     = $title,
            s.text      = $text,
            s.chapter   = $chapter,
            s.year      = $year,
            s.alt_id    = $alt_id
    """,
        sid=sid,
        act=sec.get("act", ""),
        number=sec.get("section_number", 0),
        title=sec.get("section_title", ""),
        text=sec.get("section_text", "")[:2000],  # truncate for neo4j property limits
        chapter=sec.get("chapter_title", ""),
        year=sec.get("year", 0),
        alt_id=alt_id,
    )


def link_section_to_statute(tx, section_id, statute_name):
    """Create BELONGS_TO relationship between SECTION and STATUTE."""
    tx.run("""
        MATCH (s:SECTION {section_id: $sid})
        MATCH (st:STATUTE {name: $statute})
        MERGE (s)-[:BELONGS_TO]->(st)
    """, sid=section_id, statute=statute_name)


def create_case_node(tx, case_data, file_id):
    """MERGE a CASE node from an InIRAC JSON dict."""
    c = case_data.get("case", {})
    name_raw = c.get("name", "")
    # Truncate bloated name fields to a reasonable length
    name = name_raw[:300] if name_raw else file_id
    tx.run("""
        MERGE (c:CASE {file_id: $file_id})
        SET c.name       = $name,
            c.court      = $court,
            c.year       = $year,
            c.bench_type = $bench_type,
            c.outcome    = $outcome,
            c.confidence = $confidence
    """,
        file_id=file_id,
        name=name,
        court=c.get("court", ""),
        year=c.get("year", 0),
        bench_type=c.get("bench_type", ""),
        outcome=case_data.get("outcome_type", ""),
        confidence=case_data.get("extraction_confidence", 0),
    )


def create_rule_node(tx, rule_text, case_file_id):
    """Create a RULE node and link it to its parent CASE."""
    if not rule_text or not rule_text.strip():
        return
    tx.run("""
        MERGE (r:RULE {text: $text})
        WITH r
        MATCH (c:CASE {file_id: $fid})
        MERGE (c)-[:ESTABLISHES]->(r)
    """, text=rule_text[:500], fid=case_file_id)


# ──────────────────────────────────────────────
# Edge creators
# ──────────────────────────────────────────────

def create_section_edge(tx, source_id, target_id, edge_type, props=None):
    """Create a typed relationship between two SECTION nodes."""
    props = props or {}
    query = f"""
        MATCH (a:SECTION) WHERE a.section_id = $src OR a.alt_id = $src
        MATCH (b:SECTION) WHERE b.section_id = $tgt OR b.alt_id = $tgt
        MERGE (a)-[r:{edge_type}]->(b)
        SET r += $props
    """
    tx.run(query, src=source_id, tgt=target_id, props=props)


def create_case_cites_case(tx, src_fid, cited_name):
    """CASE -[:CITES]-> CASE (by fuzzy name match on precedent string)."""
    tx.run("""
        MATCH (a:CASE {file_id: $src})
        MATCH (b:CASE) WHERE b.name CONTAINS $cited
        WHERE a <> b
        MERGE (a)-[:CITES]->(b)
    """, src=src_fid, cited=cited_name[:200])


def create_case_interprets_section(tx, case_src, section_id, weight=1.0):
    """CASE -[:INTERPRETS]-> SECTION from judgment_edges."""
    tx.run("""
        MATCH (c:CASE {file_id: $src})
        MATCH (s:SECTION {section_id: $sid})
        MERGE (c)-[r:INTERPRETS]->(s)
        SET r.weight = $w
    """, src=case_src, sid=section_id, w=weight)


# ──────────────────────────────────────────────
# Loaders
# ──────────────────────────────────────────────

STATUTE_MAP = {
    "bns_sections.json":  "BNS 2023",
    "ipc_sections.json":  "IPC 1860",
    "bnss_sections.json": "BNSS 2023",
    "bsa_sections.json":  "BSA 2023",
}

STATUTE_YEARS = {
    "BNS 2023": 2023, "IPC 1860": 1860,
    "BNSS 2023": 2023, "BSA 2023": 2023,
}


def load_sections(session):
    """Load all GovIntel section files into SECTION + STATUTE nodes."""
    for fname, statute_name in STATUTE_MAP.items():
        fpath = SECTIONS_DIR / fname
        if not fpath.exists():
            console.print(f"[yellow]⚠ Skipping missing: {fname}[/]")
            continue
        sections = json.loads(fpath.read_text(encoding="utf-8"))
        console.print(f"[cyan] Loading {len(sections)} sections from {fname}[/]")

        # Create statute node first
        session.execute_write(create_statute_node, statute_name, STATUTE_YEARS[statute_name])

        for sec in track(sections, description=f"  {statute_name}"):
            session.execute_write(create_section_node, sec)
            sid = sec.get("section_id", "")
            if sid:
                session.execute_write(link_section_to_statute, sid, statute_name)


def load_inirac_cases(session):
    """Load InIRAC judgment files into CASE + RULE nodes."""
    files = sorted(INIRAC_DIR.glob("*.json"))
    console.print(f"[cyan] Loading {len(files)} InIRAC cases[/]")
    for f in track(files, description="  Cases"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        file_id = f.stem  # e.g. "ik_10003879_irac"
        session.execute_write(create_case_node, data, file_id)

        # Create RULE nodes from extracted rules
        for rule in data.get("rules", []):
            rule_text = rule if isinstance(rule, str) else rule.get("text", "")
            session.execute_write(create_rule_node, rule_text, file_id)

        # Create CASE -[:CITES]-> CASE for cited precedents
        for prec in data.get("precedents_cited", []):
            prec_name = prec if isinstance(prec, str) else prec.get("name", "")
            if prec_name:
                session.execute_write(create_case_cites_case, file_id, prec_name)

        # Create CASE -[:INTERPRETS]-> SECTION for statutes cited
        for statute in data.get("statutes_cited", []):
            stat_name = statute if isinstance(statute, str) else statute.get("name", "")
            if stat_name:
                # Try to find matching section by name substring
                session.execute_write(
                    lambda tx, src=file_id, sn=stat_name: tx.run("""
                        MATCH (c:CASE {file_id: $src})
                        MATCH (s:SECTION) WHERE s.title CONTAINS $sn OR s.section_id CONTAINS $sn
                        MERGE (c)-[:INTERPRETS]->(s)
                    """, src=src, sn=sn[:100])
                )


def load_deterministic_edges(session):
    """Load deterministic edges (TEMPORAL_PAIR, EXPLICIT_REFERENCE, etc.)."""
    fpath = GRAPH_DIR / "deterministic_edges.json"
    if not fpath.exists():
        console.print("[yellow]⚠ No deterministic_edges.json found[/]")
        return
    edges = json.loads(fpath.read_text(encoding="utf-8"))
    console.print(f"[cyan] Loading {len(edges)} deterministic edges[/]")
    for edge in track(edges, description="  Deterministic"):
        etype = edge["edge_type"]
        props = {"direction": edge.get("direction", "")}
        session.execute_write(create_section_edge, edge["source"], edge["target"], etype, props)


def load_cross_code_edges(session):
    """Load cross-code edges (BNS<->BNSS, BNS<->BSA, etc.)."""
    fpath = GRAPH_DIR / "cross_code_edges.json"
    if not fpath.exists():
        console.print("[yellow]⚠ No cross_code_edges.json found[/]")
        return
    data = json.loads(fpath.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    console.print(f"[cyan] Loading {len(edges)} cross-code edges[/]")
    for edge in track(edges, description="  Cross-code"):
        etype = edge["edge_type"]
        props = {
            "direction": edge.get("direction", ""),
            "reason": edge.get("reason", ""),
            "confidence": edge.get("confidence", ""),
        }
        session.execute_write(create_section_edge, edge["source"], edge["target"], etype, props)


def load_autonomous_edges(session):
    """Load AI-discovered autonomous edges (ESCALATION_CHAIN, etc.)."""
    fpath = GRAPH_DIR / "autonomous_edges.json"
    if not fpath.exists():
        console.print("[yellow]⚠ No autonomous_edges.json found[/]")
        return
    data = json.loads(fpath.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    console.print(f"[cyan] Loading {len(edges)} autonomous edges[/]")
    for edge in track(edges, description="  Autonomous"):
        etype = edge["edge_type"]
        props = {
            "legal_reasoning": edge.get("legal_reasoning", "")[:500],
            "confidence": edge.get("confidence", 0),
        }
        session.execute_write(create_section_edge, edge["source"], edge["target"], etype, props)


def load_judgment_edges(session):
    """Load judgment-to-section interpretation edges."""
    fpath = GRAPH_DIR / "judgment_edges.json"
    if not fpath.exists():
        console.print("[yellow] No judgment_edges.json found[/]")
        return
    data = json.loads(fpath.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    console.print(f"[cyan] Loading {len(edges)} judgment edges[/]")

    for edge in track(edges, description="  Judgments"):
        src = edge["source"]
        tgt = edge["target"]
        weight = edge.get("weight", 1.0)
        session.execute_write(
            lambda tx, s=src, t=tgt, w=weight: tx.run("""
                MERGE (c:CASE {case_id: $src})
                WITH c
                MATCH (sec:SECTION) WHERE sec.section_id = $tgt OR sec.alt_id = $tgt
                MERGE (c)-[r:INTERPRETS]->(sec)
                SET r.weight = $w
            """, src=s, tgt=t, w=w)
        )


# ──────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────

def build():
    """Build the complete legal knowledge graph in Neo4j."""
    console.print("Building Legal Knowledge Graph")
    driver = get_driver()

    with driver.session() as session:
        # Setup constraints
        console.print("[dim]Setting up constraints & indexes...[/]")
        session.execute_write(setup_constraints)

        # Load nodes
        load_sections(session)
        load_inirac_cases(session)

        # Load edges
        load_deterministic_edges(session)
        load_cross_code_edges(session)
        load_autonomous_edges(session)
        load_judgment_edges(session)

    driver.close()
    console.print("[bold green] Graph DB built successfully.[/]")


if __name__ == "__main__":
    build()
