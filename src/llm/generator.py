"""
generator.py — Uses Ollama to paraphrase verified legal text into
conversational language.

Rules:
  - Only rewrites the verified text. Does not add facts.
  - Preserves section numbers and citations.
  - Keeps the answer in the same language as the query (if specified).
"""

import ollama

MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are a legal assistant for Indian law.

Your job is to rewrite the verified legal text below into a clear, conversational answer.

STRICT RULES:
1. Only restate what is in the verified text. Do not add any new words, conditions, or examples.
2. Do not use phrases like "without provocation", "depending on severity", or "in general" unless they appear in the source.
3. Always cite the section number and act name exactly as given.
4. Keep the answer to 2-3 sentences.
5. Do not say "based on the provided text". Answer directly.
6. Do NOT add any warning about verification. The verification status is displayed separately by the system.
"""


def generate_answer(
    query: str,
    verified_text: str,
    confidence: float,
    verified: bool,
    model: str = MODEL,
) -> str:
    """Paraphrase the verified text into a conversational answer."""

    user_prompt = f"""Question: {query}

Verified legal text:
{verified_text}

Verification status: {"VERIFIED" if verified else "UNVERIFIED"}
Confidence: {confidence:.2f}

Rewrite the verified legal text into a clear answer for the user.
"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response["message"]["content"].strip()


if __name__ == "__main__":
    # Quick test
    query = "What is the punishment for murder?"
    verified_text = """BNS 2023 Section 103: Punishment for murder
103. Punishment for murder.—(1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. (2) When a group of five or more persons acting in concert commits murder on the ground of race, caste or community, sex, place of birth, language, personal belief or any other similar ground each member of such group shall be punished with death or with imprisonment for life, and shall also be liable to fine."""

    print("=" * 70)
    print(f"Query: {query}")
    print("=" * 70)
    answer = generate_answer(query, verified_text, 0.83, True)
    print("\nGenerated answer:")
    print(answer)