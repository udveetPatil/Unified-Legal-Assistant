"""
bridge.py — Calls the translator subprocess running in venv_translation.

The main app runs in venv (new transformers). The translator runs in
venv_translation (old transformers). This bridge spawns the translator
as a subprocess and parses its JSON output.
"""

import os
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSLATION_PYTHON = PROJECT_ROOT / "venv_translation" / "Scripts" / "python.exe"


def translate_to_english(text: str, src_lang: str = "hin_Deva") -> str:
    """Call the translation subprocess for Indic to English."""
    return _call_translator("to_en", text, src_lang)


def translate_from_english(text: str, tgt_lang: str = "hin_Deva") -> str:
    """Call the translation subprocess for English to Indic."""
    return _call_translator("from_en", text, tgt_lang)


def _call_translator(mode: str, text: str, lang: str) -> str:
    """Spawn the translation venv and parse the JSON result."""
    if not TRANSLATION_PYTHON.exists():
        raise RuntimeError(
            f"Translation venv not found at {TRANSLATION_PYTHON}. "
            "Create it with: python -m venv venv_translation"
        )

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [
            str(TRANSLATION_PYTHON),
            "-m", "src.translation.translator",
            "--mode", mode,
            "--text", text,
            "--lang", lang,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode != 0:
        raise RuntimeError(f"Translation failed:\n{result.stderr}")

    # The translator prints JSON on the last non-empty line
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("Translation produced no output.")

    return json.loads(lines[-1])["result"]


# ──────────────────────────────────────────────
# Test (runs in the main venv)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing bridge from main venv...")

    hindi = "चोरी की सज़ा क्या है?"
    english = translate_to_english(hindi, "hin_Deva")
    print(f"Hindi   : {hindi}")
    print(f"English : {english}")

    back = translate_from_english("What is the punishment for murder?", "hin_Deva")
    print(f"English : What is the punishment for murder?")
    print(f"Hindi   : {back}")