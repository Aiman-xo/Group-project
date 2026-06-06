from sqlalchemy.orm import Session

from app.models.company_model import Company
from app.schemas.authentication_schema import CompanyRegister,LoginRequest,ForgotPasswordRequest,VerifyForgotPasswordOTPRequest,ResetPasswordRequest

from app.core.security import hash_password,create_access_token,create_refresh_token,verify_password
from app.core.validators import validate_password_strength

from app.service.otp_service import generate_otp,generate_forgot_password_otp,verify_forgot_password_otp
from app.utils.email import send_otp_email
from app.core.session import generate_session_id


from fastapi import BackgroundTasks,HTTPException,status
from redis.asyncio import Redis

import traceback



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
        raise HTTPException(status_code=400,detail='Email exists Try other one!')

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

    # Save company
    new_company = Company(
        email=company_data.email,
        company_name=company_data.company_name,
        website_link=company_data.website_link,
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
        return {"message":"Invalid Email and Password"}
    if not verify_password(login_data.password,company.password):
        return{
            "message":"Invalid Email and Password"
        }
    session_id = generate_session_id()

    access_token=create_access_token(
        data={
            "sub": str(company.id)  #i changed email to id for consistency bcz email can changeble
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(company.id),  #i changed email to id for consistency bcz email can changeble
            "session_id": session_id
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
        "schema_name":company.schema_name
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