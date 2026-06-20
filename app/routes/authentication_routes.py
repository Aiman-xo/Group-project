from fastapi import APIRouter,Depends,BackgroundTasks,status,Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from starlette.requests import Request

from app.schemas.authentication_schema import CompanyRegister,LoginRequest,ForgotPasswordRequest,VerifyForgotPasswordOTPRequest,ResetPasswordRequest,ResendOTPRequest
from app.service.authentication_service import register_company,login_company,forgot_password,verify_forgot_password,reset_password,resend_otp,resend_forgot_password_otp
from app.core.redis_config import get_redis
from app.schemas.authentication_schema import OTPVerifyRequest
from app.service.otp_service import verify_otp

from app.core.limiter import limiter

from redis.asyncio import Redis


router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


# @router.post("/register", status_code=status.HTTP_200_OK)
# async def register(
#     company: CompanyRegister,
#     response: Response,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     redis_client: Redis = Depends(get_redis)
# ):
    
#     result = await register_company(
#         company_data=company,
#         db=db,
#         background_tasks=background_tasks,
#         redis_client=redis_client
#     )

#     if "refresh_token" in result:
#         response.set_cookie(
#             key="refresh_token",
#             value=result["refresh_token"],
#             httponly=True,
#             secure=False,      # localhost
#             samesite="lax",
#             max_age=60 * 60 * 24 * 7
#         )

#         del result["refresh_token"]

#     return result
@router.post("/register", status_code=status.HTTP_200_OK)
async def register(
    company: CompanyRegister,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Initial registration step. Registers the company metadata, creates an unverified profile,
    and handles sending out the OTP verification mailer.
    """
    # Cleaned up: Removed the dead token check block since register_company never returns a token
    return await register_company(
        company_data=company,
        db=db,
        background_tasks=background_tasks,
        redis_client=redis_client
    )


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


# @router.post("/verify-otp", status_code=status.HTTP_200_OK)
# @limiter.limit("5/minute")
# async def verify_otp_route(
#     request: Request,
#     payload: OTPVerifyRequest,
#     response: Response,                 # <-- Added to handle HTTP-only cookie assignment
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     redis_client: Redis = Depends(get_redis)
# ):
#     """
#     Endpoint to verify a registration OTP and activate a multi-tenant business account.
#     """
#     try:
#         return await verify_otp(
#             email=payload.email, 
#             otp=payload.otp, 
#             redis_client=redis_client, 
#             db=db
#             background_tasks=background_tasks
#         )
#     except Exception as e:
#         print(f"REGISTER ERROR: {e}")   # ← this will show in terminal
#         raise

@router.post("/verify-otp", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def verify_otp_route(
    request: Request,
    payload: OTPVerifyRequest,
    response: Response,                 # Handles HTTP-only cookie assignment
    background_tasks: BackgroundTasks,   # Manages the background task pool handover
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Endpoint to verify a registration OTP and activate a multi-tenant business account.
    """
    try:
        # Await verification service layer (Passed background_tasks down successfully)
        result = await verify_otp(
            email=payload.email, 
            otp=payload.otp, 
            redis_client=redis_client, 
            db=db,
            background_tasks=background_tasks  # Fixed missing comma from your snippet
        )

        # Intercept the generated refresh token, assign to HTTP-only cookie, and strip from public JSON
        if "refresh_token" in result:
            response.set_cookie(
                key="refresh_token",
                value=result["refresh_token"],
                httponly=True,
                secure=False,      # Set to True when moving to production HTTPS
                samesite="lax",
                max_age=60 * 60 * 24 * 7
            )
            # Remove from response dictionary so Flutter client never sees it in the open body
            del result["refresh_token"]

        return result

    except Exception as e:
        print(f"REGISTER ERROR: {e}")   # Appears cleanly in your terminal log streams
        raise


@router.post("/forgot-password")
async def forgot_password_route(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    return await forgot_password(
        payload,
        db,
        redis_client,
        background_tasks
    )

@router.post("/verify-forgot-password-otp")
async def verify_forgot_password_route(
    payload: VerifyForgotPasswordOTPRequest,
    redis_client: Redis = Depends(get_redis)
):
    return await verify_forgot_password(
        payload,
        redis_client
    )

@router.post("/reset-password")
async def reset_password_route(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    return await reset_password(
        payload,
        db,
        redis_client
    )

@router.post("/resend-otp")
@limiter.limit("5/minute")
async def resend_otp_route(
    request: Request,
    payload: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    return await resend_otp(
        email=payload.email,
        db=db,
        background_tasks=background_tasks,
        redis_client=redis_client
    )

@router.post("/resend-forgot-password-otp")
async def resend_forgot_password_otp_route(
    payload: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    return await resend_forgot_password_otp(
        payload.email,
        db,
        background_tasks,
        redis_client
    )