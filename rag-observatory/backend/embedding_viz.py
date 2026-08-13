import numpy as np
import pipeline

def pca_2d(vectors: np.ndarray):
    mean = vectors.mean(axis=0)
    centered = vectors - mean
    u, s, vt = np.linalg.svd(centered, full_matrices=False)
    projected = centered @ vt.T
    return projected[:, 0], projected[:, 1]

def get_embedding_space(query: str):
    chunk_texts = pipeline.chunk_texts
    if not chunk_texts:
        return {"error": "No documents ingested yet."}

    chunk_vectors = np.array(pipeline.ollama_ef(chunk_texts))
    query_vector = np.array(pipeline.ollama_ef([query]))

    all_vectors = np.vstack([chunk_vectors, query_vector])
    x, y = pca_2d(all_vectors)

    return {
        "chunks": [
            {"text": t[:60], "x": float(x[i]), "y": float(y[i])}
            for i, t in enumerate(chunk_texts)
        ],
        "query": {"text": query, "x": float(x[-1]), "y": float(y[-1])}
    }