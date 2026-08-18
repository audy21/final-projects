# Final Projects

Things I built after the fundamentals. Six working apps, each with its own README.

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

## Support Copilot

Knowledge-base support chat with confidence-gated escalation. Streams answers grounded in company docs, hands off to a human when confidence is low, and tracks feedback in a live analytics dashboard.

**Stack:** FastAPI, ChromaDB, sentence-transformers, DeepSeek, SSE, React, Vite

[Project details](support-copilot/)

## Analis Data

Ask a company database questions in plain Indonesian and get SQL back. The LLM reads the actual schema, generates a SELECT, runs it, and the UI shows a table, summary numbers, and a chart it picked by itself. Login and history included.

**Stack:** FastAPI, SQLite, DeepSeek, JWT, Chart.js, vanilla JavaScript

[Project details](ai-data-analyst/)

## AI Data Cleaner

Upload a CSV, give cleaning instructions, and get back a cleaned file. The app previews the dataset, sends it to a generative API for cleaning code, runs the result locally, and shows before/after visuals plus a download button.

**Stack:** FastAPI, Streamlit, pandas, requests

[Project details](ai-data-cleaner/)
