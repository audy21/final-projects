import numpy as np
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

ollama_ef = embedding_functions.OllamaEmbeddingFunction(model_name="nomic-embed-text")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="rag_obs", embedding_function=ollama_ef)
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

bm25 = None
chunk_texts = []

def ingest_text(text: str, doc_id: str):
    global bm25, chunk_texts
    words = text.split()
    chunks = [" ".join(words[i:i + 400]) for i in range(0, len(words), 400)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks)
    chunk_texts = collection.get()["documents"]
    bm25 = BM25Okapi([c.lower().split() for c in chunk_texts])
    return len(chunks)

def analyze(query: str, top_k: int = 5):
    if bm25 is None:
        return {"error": "No documents ingested yet. Call /ingest first.", "telemetry": {}}
    telemetry = {}

    sem_results = collection.query(query_texts=[query], n_results=top_k)
    sem_docs = sem_results['documents'][0]
    # ChromaDB returns L2 distances (lower = closer). Normalize to similarity
    # so every layer reads as "higher = better" in the UI.
    sem_scores = [1 / (1 + d) for d in sem_results['distances'][0]]
    telemetry["semantic"] = [
        {"chunk": d, "score": round(s,4)} for d, s in zip(sem_docs, sem_scores)
    ]

    bm25_scores = bm25.get_scores(query.lower().split())
    ranked_bm25 = np.argsort(bm25_scores)[::-1][:top_k]
    telemetry["bm25"] = [
        {"chunk": chunk_texts[i], "score": round(float(bm25_scores[i]), 4)} for i in ranked_bm25
    ]

    rrf_scores = {}
    for rank, doc in enumerate(sem_docs):
        rrf_scores[doc] = rrf_scores.get(doc, 0) + 1 / (60 + rank + 1)
    for rank, i in enumerate(ranked_bm25):
        doc = chunk_texts[i]
        rrf_scores[doc] = rrf_scores.get(doc, 0) + 1 / (60 + rank + 1)
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    telemetry["rrf"] = [{"chunk": d, "score": round(s, 5)} for d, s in fused]

    pairs = [(query, d) for d, _ in fused]
    rerank_scores = [float(s) for s in cross_encoder.predict(pairs)]
    reranked = sorted(zip([d for d, _ in fused], rerank_scores), key=lambda x: x[1], reverse=True)
    telemetry["rerank"] = [{"chunk": d, "score": round(s, 5)} for d, s in reranked]

    context = "\n\n".join([d for d, _ in reranked])
    telemetry["final_context"] = context
    return telemetry