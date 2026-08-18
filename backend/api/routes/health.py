from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェック"""
    return HealthResponse(status="healthy")
