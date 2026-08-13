from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder
import time
import uuid
from sse_starlette.sse import EventSourceResponse
import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here"),
    base_url="https://api.deepseek.com/v1"
)

app = FastAPI(title="Support Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ollama_ef = embedding_functions.OllamaEmbeddingFunction(model_name="nomic-embed-text")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="support_kb", embedding_function=ollama_ef
)
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

CONFIDENCE_THRESHOLD = 0.55

kb_meta = {}
sessions = {}

class IngestRequest(BaseModel):
    text: str
    doc_id: str

@app.post("/kb/ingest")
def kb_ingest(request: IngestRequest):
    words = request.text.split()
    chunks = [" ".join(words[i:i+300]) for i in range(0, len(words), 300)]
    ids = [f"{request.doc_id}_{i}" for i in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks)
    kb_meta[request.doc_id] = len(chunks)
    return {"status": "ok", "doc_id": request.doc_id, "chunks": len(chunks)}

@app.get("/kb/list")
def kb_list():
    return {"documents": [{"doc_id": k, "chunks": v} for k, v in kb_meta.items()]}

@app.delete("/kb/{doc_id}")
def kb_delete(doc_id: str):
    ids = [f"{doc_id}_{i}" for i in range(kb_meta.get(doc_id, 0))]
    collection.delete(ids=ids)
    kb_meta.pop(doc_id, None)
    return {"status": "deleted", "doc_id": doc_id}

@app.get("/chat")
async def chat(query: str, session_id: str = None):
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    async def event_generator():
        # 1. Retrieve
        results = collection.query(query_texts=[query], n_results=5)
        chunks = results["documents"][0]

        # 2. Rerank + confidence
        pairs = [[query, c] for c in chunks]
        rerank_scores = [float(s) for s in cross_encoder.predict(pairs)]
        top_idx = rerank_scores.index(max(rerank_scores))
        confidence = 1 / (1 + pow(2.718, -rerank_scores[top_idx]))

        yield {
            "event": "retrieval",
            "data": json.dumps({
                "chunks_found": len(chunks),
                "confidence": round(confidence, 3)
            })
        }

        # 3. Escalate if below threshold
        if confidence < CONFIDENCE_THRESHOLD:
            yield {
                "event": "escalate",
                "data": json.dumps({
                    "message": "This needs a human.",
                    "confidence": round(confidence, 3)
                })
            }
            sessions[session_id] = {
                "query": query, "confidence": round(confidence, 3),
                "escalated": True, "rating": None, "ts": time.time()
            }
            return

        # 4. Stream answer from DeepSeek
        context = chunks[top_idx]
        yield {
            "event": "context",
            "data": json.dumps({"chunk": context[:200]})
        }

        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a support agent. Answer using ONLY the knowledge base below. "
                        "Keep it short and direct. If the answer is not in the knowledge base, "
                        "say so clearly.\n\nKnowledge base:\n" + context
                    )
                },
                {"role": "user", "content": query}
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {"event": "token", "data": chunk.choices[0].delta.content}

        yield {"event": "done", "data": json.dumps({"session_id": session_id})}

        sessions[session_id] = {
            "query": query, "confidence": round(confidence, 3),
            "escalated": False, "rating": None, "ts": time.time()
        }

    return EventSourceResponse(event_generator())

class FeedbackRequest(BaseModel):
    session_id: str
    rating: str  # "up" or "down"

@app.post("/feedback")
def feedback(request: FeedbackRequest):
    if request.session_id in sessions:
        sessions[request.session_id]["rating"] = request.rating
    return {"status": "ok"}

@app.get("/analytics")
def analytics():
    all_sessions = list(sessions.values())
    total = len(all_sessions)
    escalated = sum(1 for s in all_sessions if s["escalated"])
    rated = [s for s in all_sessions if s["rating"]]
    thumbs_up = sum(1 for s in rated if s["rating"] == "up")
    return {
        "total_queries": total,
        "escalation_rate": round(escalated / total, 3) if total else 0,
        "satisfaction_rate": round(thumbs_up / len(rated), 3) if rated else None,
        "recent": all_sessions[-10:]
    }