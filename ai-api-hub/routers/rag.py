from fastapi import APIRouter, Depends
from services.llm import client
from models.schemas import IngestRequest, RAGRequest, RAGResponse
from services.auth import verify_key
from services.rate_limiter import check_rate_limit
import chromadb
from chromadb.utils import embedding_functions

router = APIRouter(prefix="/rag", tags=["RAG"])

chroma_client = chromadb.PersistentClient(path="./chroma_db")
ollama_ef = embedding_functions.OllamaEmbeddingFunction(model_name="nomic-embed-text")
collection = chroma_client.get_or_create_collection(name="api_hub_docs", embedding_function=ollama_ef)

@router.post("/ingest")
def ingest(request: IngestRequest, user=Depends(verify_key), _=Depends(check_rate_limit)):
    words = request.text.split()
    chunks = [" ".join(words[i:i+500]) for i in range(0, len(words), 500)]
    ids = [f"{request.document_id}_{i}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks)
    return {"status": "ingested", "document_id": request.document_id, "chunks": len(chunks)}

@router.post("", response_model=RAGResponse)
def rag(request: RAGRequest, user=Depends(verify_key), _=Depends(check_rate_limit)):
    results = collection.query(query_texts=[request.question], n_results=request.top_k)
    sources = results["documents"][0]
    context = "\n\n".join(sources)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"Answer using only this context. If not found, say so.\n\n{context}"},
            {"role": "user", "content": request.question}
        ]
    )
    return RAGResponse(
        answer=response.choices[0].message.content,
        sources=sources
    )
