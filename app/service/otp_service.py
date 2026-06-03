import pyotp
import redis.asyncio as redis
from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.models.company_model import Company

from app.core.config import OTP_EXPIRY
  

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
    await redis_client.setex(f"otp:{email}", OTP_EXPIRY, otp) 

    return otp


async def verify_otp(email: str, otp: str, redis_client: redis.Redis,db: Session):
    """
    Verifies the OTP for the given email.
    """
    # 1. Fetch OTP from Redis (returns bytes or None)
    stored_otp_bytes = await redis_client.get(f"otp:{email}")

    # 2. Check if OTP has expired or never existed
    if not stored_otp_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="OTP has expired or never existed. Please request a new one."
        )

    # 3. Decode Redis bytes to string for accurate comparison 
    if stored_otp_bytes != otp:
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

    # 6. Activate the account
    company.is_verified = True
    db.commit()

    # 7. Delete OTP from Redis so it cannot be reused (Replay attack defense)
    await redis_client.delete(f"otp:{email}")
    
    return {"message": "OTP verified successfully. Account activated!"}