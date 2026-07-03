import json
from fastapi import APIRouter, HTTPException
import redis.asyncio as redis
from app.core.config import REDIS_URL

router = APIRouter(prefix="/progress", tags=["Progress"])

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

@router.get("/{company_id}")
async def get_crawl_progress(company_id: str):
    progress_data = await redis_client.get(
        f"crawl_progress:{company_id}"
    )

    if not progress_data:
        raise HTTPException(
            status_code=404,
            detail="No active progress found"
        )

    return json.loads(progress_data)