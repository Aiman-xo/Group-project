import json
from app.core.config import REDIS_URL
import redis

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

def update_progress(company_id: str, progress: int, status: str):
    key = f"crawl_progress:{company_id}"

    payload = {
        "progress": progress,
        "status": status
    }

    redis_client.set(
        key,
        json.dumps(payload),
        ex=3600   # auto delete after 1 hour
    )