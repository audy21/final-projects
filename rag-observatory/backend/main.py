from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline import ingest_text, analyze
from embedding_viz import get_embedding_space

app = FastAPI(title="RAG Pipeline Observatory")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    text: str
    doc_id: str

class AnalyzeRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/ingest")
def ingest(request: IngestRequest):
    count = ingest_text(request.text, request.doc_id)
    return {"status": "ok", "chunks": count}

@app.post("/analyze")
def analyze_endpoint(request: AnalyzeRequest):
    try:
        return analyze(request.query, request.top_k)
    except Exception as e:
        return {"status": "error", "detail": str(e), "type": type(e).__name__}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/embedding-space")
def embedding_space(query: str):
    return get_embedding_space(query)