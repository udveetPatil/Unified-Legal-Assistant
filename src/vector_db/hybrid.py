"""
Hybrid Merger: combines Vector DB and BM25 results using Reciprocal Rank Fusion (RRF).

RRF formula: score(d) = sum over retrievers of 1 / (k + rank(d))
where k is a constant (typically 60).

This gives a single ranked list from multiple retrievers without needing
to normalize their different score scales.
"""

from src.classifier.intent import QueryIntent


RRF_K = 60  # Standard constant for Reciprocal Rank Fusion


def reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    k: int = RRF_K,
) -> list[dict]:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.

    Args:
        vector_results: Ranked list from VectorRetriever.retrieve()
        bm25_results:   Ranked list from BM25Retriever.retrieve()
        k:              RRF constant (default 60)

    Returns:
        Merged and re-ranked list of candidates, deduplicated by id.
    """
    scores = {}
    doc_map = {}

    # ----- Score vector results -----
    for rank, doc in enumerate(vector_results):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    # ----- Score BM25 results -----
    for rank, doc in enumerate(bm25_results):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        if doc_id not in doc_map:
            doc_map[doc_id] = doc

    # ----- Sort by fused score -----
    merged = sorted(
        doc_map.values(),
        key=lambda d: scores[d["id"]],
        reverse=True,
    )

    # ----- Attach fused score -----
    for doc in merged:
        doc["rrf_score"] = scores[doc["id"]]

    return merged


class HybridRetriever:
    def __init__(self, vector_retriever, bm25_retriever):
        self.vector = vector_retriever
        self.bm25 = bm25_retriever

    def retrieve(
        self,
        intent: QueryIntent,
        top_k_per_retriever: int = 20,
        final_k: int = 20,
    ) -> list[dict]:
        """
        Retrieve from both retrievers, fuse results, return top final_k.
        """
        vector_results = self.vector.retrieve(intent, top_k=top_k_per_retriever)
        bm25_results = self.bm25.retrieve(intent, top_k=top_k_per_retriever)

        merged = reciprocal_rank_fusion(vector_results, bm25_results)
        return merged[:final_k]


if __name__ == "__main__":
    from src.classifier.intent import classify
    from src.vector_db.retriever import VectorRetriever
    from src.vector_db.bm25_retriever import BM25Retriever

    vector = VectorRetriever()
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(vector, bm25)

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
        results = hybrid.retrieve(intent, final_k=5)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [rrf={r['rrf_score']:.5f}] "
                  f"{r['metadata'].get('act')} "
                  f"Sec {r['metadata'].get('section_number')} "
                  f"({r['metadata'].get('source')})")
            print(f"     {r['text'][:120]}...")