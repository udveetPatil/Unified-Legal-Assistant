"""
Vector Retriever with metadata filtering.
Uses the Intent Classifier to apply filters before searching ChromaDB.
"""

import chromadb
from sentence_transformers import SentenceTransformer
from src.classifier.intent import QueryIntent


class VectorRetriever:
    def __init__(self, db_path: str = "data/processed/vector_db",
                 collection_name: str = "criminal"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(collection_name)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _build_where_filter(self, intent: QueryIntent) -> dict | None:
        """Build a ChromaDB where filter from the intent."""
        conditions = []

        if intent.act:
            conditions.append({"act": intent.act})
        if intent.section_number:
            conditions.append({"section_number": intent.section_number})
        if intent.question_type:
            conditions.append({"question_type": intent.question_type})

        if len(conditions) == 0:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def retrieve(self, intent: QueryIntent, top_k: int = 20) -> list[dict]:
        """Retrieve top_k candidates from ChromaDB."""
        query_embedding = self.model.encode(intent.raw_query).tolist()
        where_filter = self._build_where_filter(intent)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        candidates = []
        for doc, meta, dist, doc_id in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            results["ids"][0],
        ):
            candidates.append({
                "id": doc_id,
                "text": doc,
                "metadata": meta,
                "vector_distance": dist,
                "source": "vector",
            })

        return candidates


# ----- Test -----
if __name__ == "__main__":
    from src.classifier.intent import classify

    retriever = VectorRetriever()

    test_queries = [
        "What is the punishment for murder?",
        "What does Section 103 of BNS say?",
        "What was the punishment for murder in 2010?",
    ]

    for q in test_queries:
        intent = classify(q)
        print(f"\nQuery: {q}")
        print(f"Filter: {retriever._build_where_filter(intent)}")
        results = retriever.retrieve(intent, top_k=5)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['vector_distance']:.4f}] {r['metadata'].get('act')} "
                  f"Sec {r['metadata'].get('section_number')} "
                  f"({r['metadata'].get('source')})")
            print(f"     {r['text'][:120]}...")