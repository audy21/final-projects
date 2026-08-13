# Final Projects

Things I built after the fundamentals. Three working apps, each with its own README.

## AI API Hub

One API for five AI capabilities — chat, document Q&A, structured extraction, and a research agent. API keys, rate limiting, and a Streamlit developer portal included.

**Stack:** FastAPI, LangChain, LangGraph, ChromaDB, DeepSeek, DuckDuckGo, Streamlit

[Project details](ai-api-hub/)

## API Sandbox Generator

Paste an OpenAPI spec, get a sandbox to test it. Parses endpoints, generates mock responses with $ref resolution, and ships with a UI.

**Stack:** FastAPI, PyYAML, Streamlit

[Project details](api-sandbox/)

## RAG Pipeline Observatory

See a RAG query run layer by layer — semantic search, BM25, RRF fusion, cross-encoder reranking. Then the context it produces, and where every chunk sits in embedding space.

**Stack:** FastAPI, ChromaDB, rank-bm25, sentence-transformers, React, Vite, recharts

[Project details](rag-observatory/)
