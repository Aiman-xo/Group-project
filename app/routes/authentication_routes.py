from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.schemas.authentication_schema import CompanyRegister,LoginRequest
from app.service.authentication_service import register_company,login_company

from app.core.redis_config import get_redis
from redis.asyncio import Redis

router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register")
async def register(
    company: CompanyRegister,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    return await register_company(
        company_data=company,
        db=db,
        redis_client=redis_client
    )

@router.post("/login")
async def login(
    login_data:LoginRequest,db:Session=Depends(get_db),redis_client: Redis = Depends(get_redis)
):
    return await login_company(
        login_data,db,redis_client=redis_client
    )