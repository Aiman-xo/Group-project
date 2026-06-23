from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL=os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
REDIS_URL=os.getenv('REDIS_URL')

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)

REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
)

GROQ_API_KEY = str(os.getenv('GROQ_API_KEY'))


OTP_EXPIRY = int(os.getenv('OTP_EXPIRY'))

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = str(os.getenv('AWS_REGION'))
AWS_STORAGE_BUCKET_NAME = str(os.getenv('AWS_STORAGE_BUCKET_NAME'))
S3_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "*.lvh.me:5173"
]
