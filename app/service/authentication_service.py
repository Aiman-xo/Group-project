from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.company_model import Company
from app.schemas.authentication_schema import CompanyRegister,LoginRequest

from app.core.security import hash_password,create_access_token,create_refresh_token,verify_password
from app.core.multitenancy import create_tenant_schema_tables
from app.service.otp_service import generate_otp
from app.utils.email import send_otp_email

from fastapi import BackgroundTasks,HTTPException,status
from redis.asyncio import Redis

from app.core.session import generate_session_id



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
    # Generate tenant schema name
    safe_schema = (
        f"tenant_{company_data.company_name.lower().replace(' ', '_')}"
    )

    try:
        # Create schema physically in postgres
        db.execute(
            text(
                f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'
            )
        )

        db.commit()

        # Run tenant migration
        create_tenant_schema_tables(
            safe_schema
        )
    except Exception as e:
        db.execute(text(f'DROP SCHEMA IF EXISTS "{safe_schema}" CASCADE'))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database workspace allocation failed: {str(e)}"
        )

    try:
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
            schema_name=safe_schema
        )

        db.add(new_company)

        db.commit()

        db.refresh(new_company)

        otp = await generate_otp(company_data.email, redis_client)
        await send_otp_email(company_data.email, otp, background_tasks)
    
    except Exception as e:
        # CRITICAL SAFETY: Cascade drop schema if secondary integrations like Redis fail mid-process
        db.execute(text(f'DROP SCHEMA IF EXISTS "{safe_schema}" CASCADE'))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration process interrupted: {str(e)}"
        )

    session_id = generate_session_id()

    access_token = create_access_token(
        data={
            "sub": str(new_company.id)  #i changed email to id for consistency bcz email can changeble
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(new_company.id),  #i changed email to id for consistency bcz email can changeble
            "session_id": session_id
        }
    )
    await redis_client.set(
        f"refresh:{new_company.id}:{session_id}",
        refresh_token,
        ex=60 * 60 * 24 * 7
    )


    return {
        "message": "Company registered successfully, Please verify your OTP",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "schema_name": safe_schema
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

