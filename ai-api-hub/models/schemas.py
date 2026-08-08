from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    model: str = "deepseek-chat"
    system_prompt: Optional[str] = "You are a helpful assistant."

class ChatResponse(BaseModel):
    reply: str
    model: str
    token_used: int

class IngestRequest(BaseModel):
    text: str
    document_id: str

class RAGRequest(BaseModel):
    question: str
    top_k: int = 3

class RAGResponse(BaseModel):
    answer: str
    sources: list[str]

class ExtractRequest(BaseModel):
    text: str
    fields: str

class ExtractResponse(BaseModel):
    result: dict

class AgentRequest(BaseModel):
    question: str

class AgentResponse(BaseModel):
    answer: str
    sources: list[str]