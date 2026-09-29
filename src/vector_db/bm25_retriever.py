"""
BM25 Retriever for keyword-based search (Level 2).

Loads all documents from ChromaDB, builds a BM25 index,
and returns top-K keyword matches with metadata filtering.
"""

import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

from src.classifier.intent import QueryIntent


class BM25Retriever:
    def __init__(
        self,
        db_path: str = "data/processed/vector_db",
        collection_name: str = "criminal",
        cache_path: str = "data/processed/bm25_index.pkl",
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        self.cache_path = Path(cache_path)

        # ----- Load documents from ChromaDB -----
        print("Loading documents from ChromaDB...")
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection(collection_name)

        results = collection.get(include=["documents", "metadatas"])

        self.ids = results["ids"]
        self.documents = results["documents"]
        self.metadatas = results["metadatas"]

        print(f"  Loaded {len(self.documents)} documents")

        # ----- Build or load BM25 index -----
        if self.cache_path.exists():
            print(f"Loading cached BM25 index from {self.cache_path}...")
            with open(self.cache_path, "rb") as f:
                self.bm25 = pickle.load(f)
        else:
            print("Building BM25 index (this may take a minute)...")
            tokenized_corpus = [self._tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)

            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "wb") as f:
                pickle.dump(self.bm25, f)
            print(f"  Cached BM25 index to {self.cache_path}")

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lowercase tokenization."""
        return text.lower().split()

    def _build_where_filter(self, intent: QueryIntent) -> dict | None:
        """Build a metadata filter from the intent (same logic as VectorRetriever)."""

        # ----- Legal type determines source preference -----
        if intent.legal_type == "procedural":
            base_filter = {"source": "crpc_qa"}
        elif intent.legal_type == "substantive":
            base_filter = {"source": {"$ne": "crpc_qa"}}
        else:
            base_filter = None

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

    def _matches_filter(self, metadata: dict, intent: QueryIntent) -> bool:
        """Check if a document matches the intent's metadata filters."""
        # ----- Legal type filter -----
        if intent.legal_type == "procedural":
            if metadata.get("source") != "crpc_qa":
                return False
        elif intent.legal_type == "substantive":
            if metadata.get("source") == "crpc_qa":
                return False

        # ----- Act filter -----
        if intent.act and metadata.get("act") != intent.act:
            return False

        # ----- Section filter -----
        if intent.section_number and metadata.get("section_number") != intent.section_number:
            return False

        return True

    def retrieve(self, intent: QueryIntent, top_k: int = 20) -> list[dict]:
        """Retrieve top_k candidates using BM25."""
        tokenized_query = self._tokenize(intent.raw_query)
        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.ids, self.documents, self.metadatas, scores),
            key=lambda x: x[3],
            reverse=True,
        )

        candidates = []
        for doc_id, doc, meta, score in ranked:
            if not self._matches_filter(meta, intent):
                continue
            if score <= 0:
                continue
            candidates.append({
                "id": doc_id,
                "text": doc,
                "metadata": meta,
                "bm25_score": float(score),
                "source": "bm25",
            })
            if len(candidates) >= top_k:
                break

        return candidates


if __name__ == "__main__":
    from src.classifier.intent import classify

    retriever = BM25Retriever()

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
        results = retriever.retrieve(intent, top_k=5)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [score={r['bm25_score']:.2f}] {r['metadata'].get('act')} "
                  f"Sec {r['metadata'].get('section_number')} "
                  f"({r['metadata'].get('source')})")
            print(f"     {r['text'][:120]}...")