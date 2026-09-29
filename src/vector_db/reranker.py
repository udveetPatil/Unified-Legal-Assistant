"""
Cross-Encoder Re-ranker (Level 3).

After hybrid retrieval, take the top-N candidates and re-score them
using a cross-encoder model. Unlike embedding similarity (bi-encoder),
the cross-encoder reads the (query, document) pair together and
produces a much more accurate relevance score.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, small, ~80MB)
"""

from sentence_transformers import CrossEncoder

from src.classifier.intent import QueryIntent


DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        print(f"Loading cross-encoder: {model_name}")
        self.model = CrossEncoder(model_name)
        print("  Cross-encoder loaded")

    def rerank(
        self,
        intent: QueryIntent,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Re-score candidates with the cross-encoder and return top_k.

        Args:
            intent:     The classified query intent.
            candidates: Merged candidates from hybrid retrieval.
            top_k:      How many to return after re-ranking.

        Returns:
            Re-ranked list of candidates with 'rerank_score' added.
        """
        if not candidates:
            return []

        # Build (query, document) pairs
        query = intent.raw_query
        pairs = [(query, doc["text"]) for doc in candidates]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Attach scores
        for doc, score in zip(candidates, scores):
            doc["rerank_score"] = float(score)

        # Sort by re-rank score (descending)
        reranked = sorted(candidates, key=lambda d: d["rerank_score"], reverse=True)

        return reranked[:top_k]


if __name__ == "__main__":
    from src.classifier.intent import classify
    from src.vector_db.retriever import VectorRetriever
    from src.vector_db.bm25_retriever import BM25Retriever
    from src.vector_db.hybrid import HybridRetriever

    vector = VectorRetriever()
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(vector, bm25)
    reranker = CrossEncoderReranker()

    test_queries = [
        "What is the punishment for murder?",
        "What does Section 103 of BNS say?",
        "How do I file an FIR?",
        "What was the punishment for murder in 2010?",
        "My friend was arrested without a warrant. What are his rights?",
    ]

    for q in test_queries:
        intent = classify(q)
        print(f"\nQuery: {q}")
        print(f"Legal type: {intent.legal_type}")

        # Hybrid retrieval (top 20 candidates)
        candidates = hybrid.retrieve(intent, top_k_per_retriever=20, final_k=20)

        # Cross-encoder re-ranking (top 5)
        results = reranker.rerank(intent, candidates, top_k=5)

        for i, r in enumerate(results, 1):
            print(f"  {i}. [rerank={r['rerank_score']:.4f}] "
                  f"{r['metadata'].get('act')} "
                  f"Sec {r['metadata'].get('section_number')} "
                  f"({r['metadata'].get('source')})")
            print(f"     {r['text'][:120]}...")