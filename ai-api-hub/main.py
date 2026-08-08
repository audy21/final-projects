from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from routers import chat, rag, extract, agent, auth

app = FastAPI(title="AI API Hub", description="CPaaS for AI - chat, RAG, extract, agent.")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AI API Hub",
        version="1.0.0",
        description="CPaaS for AI - chat, RAG, extract, agent.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
            "description": "API key from /auth/keys"
        }
    }
    openapi_schema["security"] = [{"ApiKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(extract.router)
app.include_router(agent.router)
app.include_router(auth.router)

active_requests = {}

@app.get("/health")
def health():
    return {"status": "ok", "service": "AI API Hub"}

@app.get("/usage")
def usage():
    return {"total_requests": len(active_requests)}
