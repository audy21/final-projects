import uuid
from fastapi import HTTPException, Header

api_keys = {}

def generate_key(user: str) -> str:
     key = f"sk-{uuid.uuid4().hex[:24]}"
     api_keys[key] = {"user": user, "active": True}
     return key

def verify_key(x_api_key: str = Header(None)) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if x_api_key not in api_keys or not api_keys[x_api_key]["active"]:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_keys[x_api_key]["user"]