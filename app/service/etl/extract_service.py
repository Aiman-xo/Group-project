import json
import boto3
from app.core.logger import logger
from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME
)

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def download_from_s3(key: str) -> str:
    """
    Downloads file from S3 and returns raw content as string.
    key = "company/infosys/admin/crawled_infosys.txt"
    """
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        content = response["Body"].read().decode("utf-8")
        return content
    except Exception as e:
        logger.error(f"Failed to download from S3: {key} | Error: {str(e)}")
        return ""

# This function takes the key from redis and if the file ends with json then it converts it into readable dict format and if it is txt then return as it it
# Because the txt downloads as string from s3.
def extract_content_from_file(key: str) -> str:
    """
    Downloads file from S3.
    .txt  → returns raw text string
    .json → parses and returns pretty printed string for LLM
    """
    raw_content = download_from_s3(key)  # always a string from S3

    if not raw_content:
        logger.warning(f"Empty content for {key}, skipping.")
        return ""

    if key.endswith(".json"):
        try:
            parsed = json.loads(raw_content)         # string → dict 
            return json.dumps(parsed, indent=2)      # dict → readable string for LLM
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON for {key}, using raw content")
            return raw_content

    elif key.endswith(".txt"):
        return raw_content                           # just return 

    else:
        logger.warning(f"Unknown file type for {key}, skipping.")
        return ""