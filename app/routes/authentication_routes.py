from fastapi import APIRouter,Depends,BackgroundTasks,status
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.schemas.authentication_schema import CompanyRegister,LoginRequest
from app.service.authentication_service import register_company,login_company
from app.core.redis_config import get_redis
from app.schemas.authentication_schema import OTPVerifyRequest
from app.service.otp_service import verify_otp

from redis.asyncio import Redis

router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register",status_code=status.HTTP_200_OK)
async def register(
    company: CompanyRegister,
    background_tasks:BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client:Redis=Depends(get_redis)
):
    try:
        return await register_company(
            company_data=company,
            db=db,
            background_tasks=background_tasks,
            redis_client=redis_client
        )
    except Exception as e:
        print(f"REGISTER ERROR: {e}")   # ← this will show in terminal
        raise

@router.post("/login",status_code=status.HTTP_200_OK)
def login(login_data:LoginRequest,db:Session=Depends(get_db)):
    return login_company(login_data,db)


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp_route(
    request: OTPVerifyRequest,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Endpoint to verify a registration OTP and activate a multi-tenant business account.
    """
    try:
        return await verify_otp(
            email=request.email, 
            otp=request.otp, 
            redis_client=redis_client, 
            db=db
        )
    except Exception as e:
        print(f"REGISTER ERROR: {e}")   # ← this will show in terminal
        raise