from fastapi import APIRouter,Depends,BackgroundTasks,status,Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from starlette.requests import Request

from app.schemas.authentication_schema import CompanyRegister,LoginRequest
from app.service.authentication_service import register_company,login_company
from app.core.redis_config import get_redis
from app.schemas.authentication_schema import OTPVerifyRequest
from app.service.otp_service import verify_otp

from app.core.limiter import limiter

from redis.asyncio import Redis


router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(
    company: CompanyRegister,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    
    result = await register_company(
        company_data=company,
        db=db,
        background_tasks=background_tasks,
        redis_client=redis_client
    )

    if "refresh_token" in result:
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=False,      # localhost
            samesite="lax",
            max_age=60 * 60 * 24 * 7
        )

        del result["refresh_token"]

    return result



@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    
    result = await login_company(
        login_data,
        db,
        redis_client
    )

    if "refresh_token" in result:
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=False,      # localhost development
            samesite="lax",
            max_age=60 * 60 * 24 * 7
        )

        # Don't send refresh token in response body
        del result["refresh_token"]

    return result


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def verify_otp_route(
    request: Request,
    payload: OTPVerifyRequest,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Endpoint to verify a registration OTP and activate a multi-tenant business account.
    """
    try:
        return await verify_otp(
            email=payload.email, 
            otp=payload.otp, 
            redis_client=redis_client, 
            db=db
        )
    except Exception as e:
        print(f"REGISTER ERROR: {e}")   # ← this will show in terminal
        raise
