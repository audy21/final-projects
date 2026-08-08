from fastapi import APIRouter, Depends
from services.llm import client
from models.schemas import ExtractRequest, ExtractResponse
from services.auth import verify_key
from services.rate_limiter import check_rate_limit
import json

router = APIRouter(prefix="/extract", tags=["Extract"])

@router.post("", response_model=ExtractResponse)
def extract(request: ExtractRequest, user=Depends(verify_key), _=Depends(check_rate_limit)):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a structured data extractor. Return ONLY valid JSON. No markdown, no explanation."},
            {"role": "user", "content": f"Extract these fields as JSON: {request.fields}\n\nText: {request.text}"}
        ]
    )
    data = json.loads(response.choices[0].message.content)
    return ExtractResponse(result=data)
