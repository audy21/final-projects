from fastapi import APIRouter
from pydantic import BaseModel
from services.auth import generate_key, api_keys

router = APIRouter(prefix="/auth", tags=["Auth"])

class KeyRequest(BaseModel):
    user: str

class KeyResponse(BaseModel):
    api_key: str
    user: str

@router.post("/keys", response_model=KeyResponse)
def create_key(request: KeyRequest):
    key = generate_key(request.user)
    return KeyResponse(api_key=key, user=request.user)

@router.get("/keys")
def list_keys():
    return {"keys": list(api_keys.keys()), "total": len(api_keys)}