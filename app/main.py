from fastapi import FastAPI
import redis.asyncio as redis
import logging
from contextlib import asynccontextmanager
from app.core.redis_config import init_redis_pool,redis_pool
from app.routes.authentication_routes import router as auth_router
from app.routes.company_routes import router as company_router

# Rate Limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import ALLOWED_ORIGINS

#Celery
from app.core.celery_config import celery_app


@asynccontextmanager
async def lifespan(app:FastAPI):
    # Boot up the pool
    init_redis_pool()
    yield
    # Shut down the pool
    if redis_pool:
        await redis_pool.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://([a-z0-9-]+)\.(lvh\.me|yourproduct\.com)(:\d+)?", # added this to allow coming from the origin like lvh.me:8000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router,prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")