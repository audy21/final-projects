from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from mock_generator import generate_response
import yaml
import json
import random

app = FastAPI(title="API Sandbox Generator")

class SpecRequest(BaseModel):
    spec: str

class GenerateRequest(BaseModel):
    spec: str
    endpoint_path: str
    method: str
    status_code: str = "200"

@app.post("/parse")
def parse_spec(request: SpecRequest):
    try:
        spec = yaml.safe_load(request.spec)
        if not spec:
            spec = json.loads(request.spec)

        endpoints = []
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "request_body": details.get("requestBody", {}),
                        "responses": details.get("responses", {})
                    })

        return {"status": "parsed", "endpoints": endpoints, "total": len(endpoints)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/generate")
def generate_mock(request: GenerateRequest):
    try:
        spec = yaml.safe_load(request.spec) or json.loads(request.spec)
        method = request.method.lower()
        endpoint = spec["paths"][request.endpoint_path][method]
        response_schema = endpoint["responses"][request.status_code]["content"]["application/json"]["schema"]
        mock = generate_response(response_schema, spec)
        return {"status": "generated", "endpoint": f"{request.method.upper()} {request.endpoint_path}", "mock_response": mock}
    except Exception as e:
        return {"status": "error", "message": str(e)}