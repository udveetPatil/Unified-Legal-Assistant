"""
End-to-end retrieval pipeline.

Flow:
  Query -> Intent Classifier -> Hybrid Retrieval -> Cross-Encoder Re-ranker -> Top 5

This is the retrieval stage. It does NOT call the LLM or the Verifier yet.
"""

from src.classifier.intent import classify, QueryIntent
from src.vector_db.retriever import VectorRetriever
from src.vector_db.bm25_retriever import BM25Retriever
from src.vector_db.hybrid import HybridRetriever
from src.vector_db.reranker import CrossEncoderReranker


class RetrievalPipeline:
    def __init__(self):
        print("Initializing retrieval pipeline...")
        self.vector = VectorRetriever()
        self.bm25 = BM25Retriever()
        self.hybrid = HybridRetriever(self.vector, self.bm25)
        self.reranker = CrossEncoderReranker()
        print("Pipeline ready\n")

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Run the full retrieval pipeline.

        Returns:
            List of top_k candidates with all scores and metadata.
        """
        # Step 1: Classify
        intent = classify(query)

        # Step 2: Hybrid retrieval
        candidates = self.hybrid.retrieve(
            intent,
            top_k_per_retriever=20,
            final_k=20,
        )

        # Step 3: Cross-encoder re-ranking
        results = self.reranker.rerank(intent, candidates, top_k=top_k)

        return results, intent


if __name__ == "__main__":
    pipeline = RetrievalPipeline()

    test_queries = [
        "What is the punishment for murder?",
        "What does Section 103 of BNS say?",
        "How do I file an FIR?",
        "What was the punishment for murder in 2010?",
        "My friend was arrested without a warrant. What are his rights?",
    ]

    for q in test_queries:
        results, intent = pipeline.retrieve(q, top_k=5)
        print(f"\n{'=' * 70}")
        print(f"Query     : {q}")
        print(f"Legal type: {intent.legal_type}")
        print(f"Act       : {intent.act}")
        print(f"Section   : {intent.section_number}")
        print(f"{'=' * 70}")
        for i, r in enumerate(results, 1):
            print(f"\n  [{i}] rerank={r['rerank_score']:.4f}  "
                  f"rrf={r.get('rrf_score', 0):.5f}")
            print(f"      Source : {r['metadata'].get('source')}")
            print(f"      Act    : {r['metadata'].get('act')}")
            print(f"      Section: {r['metadata'].get('section_number')}")
            print(f"      Text   : {r['text'][:200]}...")