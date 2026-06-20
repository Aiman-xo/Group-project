from sqlalchemy.orm import Session

from app.models.company_model import Company
from app.schemas.authentication_schema import CompanyRegister,LoginRequest,ForgotPasswordRequest,VerifyForgotPasswordOTPRequest,ResetPasswordRequest

from app.core.security import hash_password,create_access_token,create_refresh_token,verify_password
from app.core.validators import validate_password_strength

from app.service.otp_service import generate_otp,generate_forgot_password_otp,verify_forgot_password_otp
from app.utils.email import send_otp_email
from app.core.session import generate_session_id
from app.core.url_utils import normalize_url


from fastapi import BackgroundTasks,HTTPException,status
from redis.asyncio import Redis

import traceback
from app.core.logger import logger


async def register_company(
    company_data: CompanyRegister,
    db: Session,
    background_tasks:BackgroundTasks,
    redis_client:Redis
):

    # Check email already exists
    existing_company = db.query(Company).filter(
        Company.email == company_data.email
    ).first()

    if existing_company:

        if existing_company.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Not verified yet
        otp = await generate_otp(
            existing_company.email,
            redis_client
        )

        await send_otp_email(
            existing_company.email,
            otp,
            background_tasks
        )

        return {
            "message": "Account exists but is not verified. New OTP sent."
        }

    if company_data.password != company_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Password and confirm password do not match"
        )
    
    validate_password_strength(
        company_data.password
    )

    # Hash password
    hashed_password = hash_password(
        company_data.password
    )

    website_link = normalize_url(
        company_data.website_link
    )

    from app.utils.slug import generate_slug
    slug = generate_slug(company_data.company_name)
    if slug in {"www", "api", "admin", "app", "help", "support", "static"}:
        raise HTTPException(
            status_code=400,
            detail="This company name is reserved. Please choose another name."
        )

    # Save company
    # Note: slug is intentionally NOT saved here. It is assigned
    # definitively during OTP verification (otp_service.py) where
    # uniqueness conflict is also handled safely with a UUID suffix fallback.
    new_company = Company(
        email=company_data.email,
        company_name=company_data.company_name,
        website_link=website_link,
        industry=company_data.industry,
        password=hashed_password,
        schema_name=None
    )

    db.add(new_company)

    db.commit()

    db.refresh(new_company)
    try:

        otp = await generate_otp(company_data.email, redis_client)
        await send_otp_email(company_data.email, otp, background_tasks)
    
    except Exception as e:
        traceback.print_exc()
        db.delete(new_company)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )



    return {
        "message": "Company registered successfully, Please verify your OTP",
    }



async def login_company(login_data:LoginRequest,db:Session,redis_client: Redis):
    company=db.query(Company).filter(Company.email==login_data.email).first()
    if not company:
        logger.warning(f"company not found! {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not verify_password(login_data.password,company.password):
         logger.warning(f"Invalid password for {login_data.email}")
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    session_id = generate_session_id()

    access_token=create_access_token(
        data={
            "sub": str(company.id),  #i changed email to id for consistency bcz email can changeble
            "slug":str(company.slug) 
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(company.id),  #i changed email to id for consistency bcz email can changeble
            "session_id": session_id,
            "slug":str(company.slug) 
        }
    )
    await redis_client.set(
        f"refresh:{company.id}:{session_id}",
        refresh_token,
        ex=60 * 60 * 24 * 7
    )

    return{
        "message":"Login Successfully",
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearer",
    }


async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session,
    redis_client: Redis,
    background_tasks: BackgroundTasks
):

    company = db.query(Company).filter(
        Company.email == payload.email
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )

    otp = await generate_forgot_password_otp(
        payload.email,
        redis_client
    )

    await send_otp_email(
        payload.email,
        otp,
        background_tasks
    )

    return {
        "message":"Password reset OTP sent"
    }

async def verify_forgot_password(
    payload: VerifyForgotPasswordOTPRequest,
    redis_client: Redis
):
    return await verify_forgot_password_otp(
        payload.email,
        payload.otp,
        redis_client
    )

async def reset_password(
    payload: ResetPasswordRequest,
    db: Session,
    redis_client: Redis
):

    allowed = await redis_client.get(
        f"reset_allowed:{payload.email}"
    )

    if not allowed:
        raise HTTPException(
            status_code=400,
            detail="OTP verification required"
        )

    company = db.query(Company).filter(
        Company.email == payload.email
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirm password do not match"
        )
    
    if verify_password(payload.new_password,company.password):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as old password"
        )

    company.password = hash_password(
        payload.new_password
    )


    db.commit()

    await redis_client.delete(
        f"reset_allowed:{payload.email}"
    )

    return {
        "message":"Password updated successfully. Please login again."
    }

async def resend_otp(
    email: str,
    db: Session,
    background_tasks: BackgroundTasks,
    redis_client: Redis
):
    company = (
        db.query(Company)
        .filter(Company.email == email)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    if company.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Account already verified"
        )

    otp = await generate_otp(
        email,
        redis_client
    )

    await send_otp_email(
        email,
        otp,
        background_tasks
    )

    return {
        "message": "OTP resent successfully"
    }

async def resend_forgot_password_otp(
    email: str,
    db: Session,
    background_tasks: BackgroundTasks,
    redis_client: Redis
):
    company = (
        db.query(Company)
        .filter(Company.email == email)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    otp = await generate_forgot_password_otp(
        email,
        redis_client
    )

    await send_otp_email(
        email,
        otp,
        background_tasks
    )

    return {
        "message": "Password reset OTP resent successfully"
    }