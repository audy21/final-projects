from fastapi import APIRouter, Depends
from services.llm import client
from models.schemas import ChatRequest, ChatResponse
from services.auth import verify_key
from services.rate_limiter import check_rate_limit

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, user=Depends(verify_key), _=Depends(check_rate_limit)):
    response = client.chat.completions.create(
        model=request.model,
        messages=[
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.message}
        ]
    )
    return ChatResponse(
        reply=response.choices[0].message.content,
        model=request.model,
        token_used=response.usage.total_tokens
    )
