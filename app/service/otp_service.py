import pyotp
import redis.asyncio as redis
from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.models.company_model import Company

from app.core.multitenancy import create_tenant_schema_tables
from app.core.security import create_access_token,create_refresh_token
from sqlalchemy import text

from app.core.session import generate_session_id


from app.core.config import OTP_EXPIRY

from app.utils.slug import generate_slug
  

async def generate_otp(email: str, redis_client: redis.Redis):
    """
    Generates a 6-digit OTP and stores it in Redis with 5 min expiry.
    """
     # generates a random secret key eg: "JBSWY3DPEHPK3PXP"
    secret = pyotp.random_base32() 
     # creates a time-based OTP generator
    totp = pyotp.TOTP(secret, interval=OTP_EXPIRY)
     # generates current 6-digit OTP eg: "482910"
    otp = totp.now()

    # set otp in the redis along with the exp time.
    await redis_client.setex(f"otp:{email}", OTP_EXPIRY, secret) 

    return otp


async def verify_otp(email: str, otp: str, redis_client: redis.Redis,db: Session):
    """
    Verifies the OTP for the given email.
    """

    attempts_key = f"otp_attempts:{email}"
    attempts = await redis_client.get(attempts_key)
    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Request a new OTP."
        )
    
    # 1. Fetch OTP from Redis (returns bytes or None)
    stored_otp_bytes = await redis_client.get(f"otp:{email}")
    

    # 2. Check if OTP has expired or never existed
    if not stored_otp_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="OTP has expired or never existed. Please request a new one."
        )

    # 3. Decode Redis bytes to string for accurate comparison 
    secret = stored_otp_bytes
    totp = pyotp.TOTP(secret, interval=OTP_EXPIRY)
    if not totp.verify(otp, valid_window=1):
        await redis_client.incr(attempts_key)
        await redis_client.expire(attempts_key, OTP_EXPIRY)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code entered."
        )

    # 4. Fetch the company profile from the public registry
    company = db.query(Company).filter(Company.email == email).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company registry record not found."
        )

    # 5. Check if already verified to prevent redundant db writes
    if company.is_verified:
        return {"message": "Account is already active. Proceed to login."}
    
    # Generate slug
    slug = generate_slug(company.company_name)

    # Check duplicate slug
    existing_slug = db.query(Company).filter(
        Company.slug == slug
    ).first()

    if existing_slug:
        slug = f"{slug}-{str(company.id)[:8]}"
        
    # Internal schema name
    safe_schema = f"tenant_{slug.replace('-', '_')}"
    
    # safe_schema = f"tenant_{company.company_name.lower().replace(' ', '_')}"
    try:
        db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'))
        db.commit()
        create_tenant_schema_tables(safe_schema)
    except Exception as e:
        db.execute(text(f'DROP SCHEMA IF EXISTS "{safe_schema}" CASCADE'))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workspace allocation failed: {str(e)}"
        )

    # 6. Activate the account
    company.is_verified = True
    company.schema_name = safe_schema
    company.slug = slug
    db.commit()
    db.refresh(company)

    # 7. Delete OTP from Redis so it cannot be reused (Replay attack defense)
    await redis_client.delete(f"otp:{email}", attempts_key)

    # await redis_client.delete(f"otp:{email}")

    session_id = generate_session_id()

    access_token = create_access_token(
        data={
            "sub": str(company.id), #i changed email to id for consistency bcz email can changeble
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
    
    return {
        "message": "OTP verified. Account activated!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

async def generate_forgot_password_otp(email: str,redis_client: redis.Redis
):
    secret = pyotp.random_base32()

    totp = pyotp.TOTP(
        secret,
        interval=OTP_EXPIRY
    )

    otp = totp.now()
    await redis_client.setex(
        f"forgot_otp:{email}",
        OTP_EXPIRY,
        secret
    )

    return otp

async def verify_forgot_password_otp(email: str,otp: str,  redis_client: redis.Redis):
    stored_secret = await redis_client.get(
        f"forgot_otp:{email}"
    )

    if not stored_secret:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    totp = pyotp.TOTP(
        stored_secret,
        interval=OTP_EXPIRY
    )

    if not totp.verify(
        otp,
        valid_window=1
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    await redis_client.setex(
        f"reset_allowed:{email}",
        300,
        "true"
    )

    await redis_client.delete(
        f"forgot_otp:{email}"
    )

    return {
        "message":"OTP verified successfully"
    }