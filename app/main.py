from fastapi import FastAPI
import redis.asyncio as redis
from contextlib import asynccontextmanager
from app.core.redis_config import init_redis_pool,redis_pool
from app.routes.authentication_routes import router as auth_router

@asynccontextmanager
async def lifespan(app:FastAPI):
    # Boot up the pool
    init_redis_pool()
    yield
    # Shut down the pool
    if redis_pool:
        await redis_pool.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)