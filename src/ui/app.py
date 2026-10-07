"""
app.py — Streamlit UI for the Unified Legal Assistant.

Run with:
    streamlit run src/ui/app.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from src.integration import IntegratedLegalAssistant


# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Unified Legal Assistant for India",
    page_icon="⚖️",
    layout="wide",
)


# ──────────────────────────────────────────────
# Cached assistant (loads once)
# ──────────────────────────────────────────────
@st.cache_resource
def get_assistant():
    return IntegratedLegalAssistant()


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.title("⚖️ Unified Legal Assistant for India")
st.caption(
    "Offline · Graph-verified · Temporal · Domain-partitioned · Multilingual (coming soon)"
)

st.markdown("---")


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        **Scope:** Criminal Law (BNS, BNSS, BSA + IPC, CrPC, IEA)

        **How it works:**
        1. Retrieves relevant law sections
        2. Verifies against the legal knowledge graph
        3. Returns answer + confidence score
        4. Flags unverified answers with a warning

        **Anti-hallucination:** Every answer is checked against a Neo4j graph of
        2,339 nodes and 5,384 edges before being returned.
        """
    )
    st.markdown("---")
    st.markdown("### Example Queries")
    examples = [
        "What is the punishment for murder?",
        "What does Section 103 of BNS say?",
        "What was the punishment for murder in 2010?",
        "How do I file an FIR?",
        "Can someone be arrested under BNS Section 999 for cyberbullying?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}"):
            st.session_state.query = ex


# ──────────────────────────────────────────────
# Query input
# ──────────────────────────────────────────────
query = st.text_input(
    "Ask a legal question:",
    value=st.session_state.get("query", ""),
    placeholder="e.g. What is the punishment for murder?",
)

col1, col2 = st.columns([1, 5])
with col1:
    ask_button = st.button("Ask", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("Clear", use_container_width=True)

if clear_button:
    st.session_state.query = ""
    st.rerun()


# ──────────────────────────────────────────────
# Process query
# ──────────────────────────────────────────────
if ask_button and query.strip():
    with st.spinner("Retrieving and verifying..."):
        assistant = get_assistant()
        result = assistant.ask(query.strip())

    st.markdown("---")
    st.subheader("Answer")

    # ----- Verified badge -----
    if result.verified:
        st.success(f"✅ Verified — Confidence: {result.confidence:.2f}")
    else:
        st.warning(f"⚠️ Low Confidence — {result.confidence:.2f}")

    # ----- Warning -----
    if result.warning:
        st.error(result.warning)

    # ----- Answer text -----
    st.markdown(result.answer)

    # ----- Verification reason -----
    with st.expander("Why this answer?"):
        st.write(result.verification_reason)

    # ----- Candidates -----
    with st.expander(f"Retrieved {len(result.candidates)} candidates"):
        for i, c in enumerate(result.candidates[:5], 1):
            meta = c.get("metadata", {})
            st.markdown(
                f"**{i}. {meta.get('act', 'Unknown Act')} — Section {meta.get('section_number', 'N/A')}**"
            )
            st.caption(f"Source: {meta.get('source', 'unknown')}")
            st.text(c.get("text", "")[:300] + "...")
            st.markdown("---")

elif ask_button:
    st.warning("Please enter a question.")


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.caption(
    "⚠️ This system provides legal information, not legal advice. "
    "Always consult a qualified lawyer for your specific situation."
)