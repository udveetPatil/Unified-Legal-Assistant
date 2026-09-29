import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="data/processed/vector_db")
collection = client.get_collection("criminal")

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "What is the punishment for murder?"
query_embedding = model.encode(query).tolist()

# With filter: only gsms-b
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"source": "gsms-b"},
)

print(f"Query: {query} (filtered to gsms-b)")
print("=" * 60)
for i, (doc, meta, dist) in enumerate(zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0],
), 1):
    print(f"\n--- Result {i} (distance: {dist:.4f}) ---")
    print(f"Act    : {meta.get('act')}")
    print(f"Section: {meta.get('section_number')}")
    print(f"Text   : {doc[:250]}...")