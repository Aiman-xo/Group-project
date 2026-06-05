from sqlalchemy.orm import Session

from app.models.company_model import Company
from app.schemas.authentication_schema import CompanyRegister,LoginRequest

from app.core.security import hash_password,create_access_token,create_refresh_token,verify_password

from app.service.otp_service import generate_otp
from app.utils.email import send_otp_email

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
def forget_password(l):
    pass

