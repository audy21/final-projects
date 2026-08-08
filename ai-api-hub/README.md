# AI API Hub

CPaaS for AI — serve multiple AI capabilities through a single API platform. Built with FastAPI, LangChain, LangGraph, ChromaDB, and DeepSeek.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /chat` | LLM chat with configurable system prompts |
| `POST /rag/ingest` | Ingest documents into the vector store |
| `POST /rag` | Ask questions against ingested documents (RAG) |
| `POST /extract` | Structured data extraction (returns JSON) |
| `POST /agent` | Autonomous research agent with web search |
| `POST /auth/keys` | Generate API keys |
| `GET /health` | Health check |

## Structure

```
ai-api-hub/
├── main.py              # App entry point
├── dashboard.py         # Streamlit developer portal
├── models/
│   └── schemas.py       # Pydantic request/response models
├── services/
│   ├── llm.py           # DeepSeek client
│   ├── auth.py          # API key management
│   └── rate_limiter.py  # Rate limiting (sliding window)
├── routers/
│   ├── chat.py          # /chat
│   ├── rag.py           # /rag + /rag/ingest
│   ├── extract.py       # /extract
│   ├── agent.py         # /agent (LangGraph + DuckDuckGo)
│   └── auth.py          # /auth
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Pull embedding model (for RAG)
ollama pull nomic-embed-text

# Set your API key
export DEEPSEEK_API_KEY="sk-your-key"

# Run the server
uvicorn main:app --reload --port 8000

# Run the dashboard (separate terminal)
streamlit run dashboard.py
```

## Features

- 5 AI endpoints served through a single API
- API key authentication (generate via `/auth/keys`)
- Rate limiting (10 req/min per key)
- Auto-generated Swagger docs at `/docs`
- Streamlit developer portal for testing

## Tech Stack

`Python` `FastAPI` `LangChain` `LangGraph` `ChromaDB` `DeepSeek` `DuckDuckGo` `Streamlit` `Pydantic`
