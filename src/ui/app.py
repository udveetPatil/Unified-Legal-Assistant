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
from src.translation.bridge import translate_to_english, translate_from_english


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
# Supported languages
# ──────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "eng_Latn": "English",
    "hin_Deva": "Hindi",
    "tam_Taml": "Tamil",
    "tel_Telu": "Telugu",
    "kan_Knda": "Kannada",
    "mal_Mlym": "Malayalam",
    "ben_Beng": "Bengali",
    "mar_Deva": "Marathi",
    "guj_Gujr": "Gujarati",
    "urd_Arab": "Urdu",
    "pan_Guru": "Punjabi",
}


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.title("⚖️ Unified Legal Assistant for India")
st.caption(
    "Offline · Graph-verified · Temporal · Domain-partitioned · Multilingual"
)

st.markdown("---")


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("Language")
    selected_lang = st.selectbox(
        "Answer language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda k: SUPPORTED_LANGUAGES[k],
        index=0,
    )
    st.markdown("---")

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
        2,479 nodes and 5,334 edges before being returned.
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

    # ----- Step 1: Translate input to English if needed -----
    query_en = query.strip()
    if selected_lang != "eng_Latn":
        with st.spinner(f"Translating from {SUPPORTED_LANGUAGES[selected_lang]}..."):
            try:
                query_en = translate_to_english(query.strip(), src_lang=selected_lang)
            except Exception as e:
                st.error(f"Input translation failed: {e}")
                st.stop()

    # ----- Step 2: Retrieve and verify -----
    with st.spinner("Retrieving and verifying..."):
        assistant = get_assistant()
        result = assistant.ask(query_en)

    # ----- Step 3: Translate the RAW LEGAL TEXT only (not the paraphrase) -----
    translated_answer = result.answer
    translation_failed = False

    if selected_lang != "eng_Latn" and result.verified:
        with st.spinner(f"Translating legal text to {SUPPORTED_LANGUAGES[selected_lang]}..."):
            try:
                translated_answer = translate_from_english(
                    result.answer, tgt_lang=selected_lang
                )
            except Exception as e:
                translation_failed = True
                st.warning(f"Output translation failed: {e}")

    # ----- Display -----
    st.markdown("---")
    st.subheader("Answer")

    # Verified badge
    if result.verified:
        st.success(f"✅ Verified — Confidence: {result.confidence:.2f}")
    else:
        st.warning(f"⚠️ Low Confidence — {result.confidence:.2f}")

    # Warning
    if result.warning:
        st.error(result.warning)

    # Show translated query if it differs from input
    if selected_lang != "eng_Latn":
        with st.expander("Show English translation of your question"):
            st.markdown(f"**You asked:** {query.strip()}")
            st.markdown(f"**In English:** {query_en}")

    # Simplified explanation (English only — LLM paraphrase is not translated)
    if result.paraphrase:
        st.markdown("**Simplified explanation (English):**")
        st.markdown(result.paraphrase)

    # Translated legal text (only when a non-English language is selected)
    if selected_lang != "eng_Latn" and not translation_failed:
        st.markdown(f"**Verified legal text ({SUPPORTED_LANGUAGES[selected_lang]}):**")
        st.markdown(translated_answer)
        st.caption(
            "Machine translation. The English text below is the authoritative source."
        )

    # English legal text (always shown)
    st.markdown("**Verified legal text (English):**")
    st.markdown(result.answer)

    # Verification reason
    with st.expander("Why this answer?"):
        st.write(result.verification_reason)

    # Candidates
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