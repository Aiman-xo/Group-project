import redis.asyncio as redis
from app.core.config import REDIS_URL

redis_pool: redis.ConnectionPool | None = None

# Initialise the redis connection with the fastapi.
def init_redis_pool():
    global redis_pool
    redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True, max_connections=10)
    return redis_pool


async def get_redis():
    """The dependency your routes will use"""
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()