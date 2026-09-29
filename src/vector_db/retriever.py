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

        # ----- Legal type determines source preference -----
        if intent.legal_type == "procedural":
            base_filter = {"source": "crpc_qa"}
        elif intent.legal_type == "substantive":
            base_filter = {"source": {"$ne": "crpc_qa"}}
        else:
            base_filter = None

        # ----- Additional filters override or combine -----
        conditions = []
        if base_filter:
            conditions.append(base_filter)
        if intent.act:
            conditions.append({"act": intent.act})
        if intent.section_number:
            conditions.append({"section_number": intent.section_number})

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


if __name__ == "__main__":
    from src.classifier.intent import classify

    retriever = VectorRetriever()

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
        print(f"Filter: {retriever._build_where_filter(intent)}")
        results = retriever.retrieve(intent, top_k=5)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['vector_distance']:.4f}] {r['metadata'].get('act')} "
                  f"Sec {r['metadata'].get('section_number')} "
                  f"({r['metadata'].get('source')})")
            print(f"     {r['text'][:120]}...")