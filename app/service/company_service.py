import httpx
import boto3

from uuid import uuid4
from fastapi import HTTPException, status, UploadFile
from app.core.url_utils import normalize_url
from sqlalchemy.orm import Session
from app.models.company_model import Company
from app.tasks.process_csv_file_task import process_uploaded_csv
from app.utils.progress_tracker import update_csv_file_upload_progress,reset_progress
from app.core.config import AWS_STORAGE_BUCKET_NAME,AWS_SECRET_ACCESS_KEY,AWS_ACCESS_KEY_ID,AWS_REGION


async def check_company_url(url: str):
    # Add protocol if user enters google.com
    url = normalize_url(url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                follow_redirects=True
            )

            #  INDENTED INSIDE: Runs safely while the client context is alive
            if response.status_code < 400 or response.status_code == 403:
                return {
                    "valid": True,
                    "message": "Website reachable"
                }

            return {
                "valid": False,
                "message": f"Website returned status code {response.status_code}"
            }

    except httpx.ConnectError:
        return {
            "valid": False,
            "message": "Unable to connect to website"
        }

    except httpx.TimeoutException:
        return {
            "valid": False,
            "message": "Website request timed out"
        }

    except httpx.InvalidURL:
        return {
            "valid": False,
            "message": "Invalid website URL"
        }

    except Exception as e:
        print(f"URL Validation Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate website URL"
        )

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
    )
async def csv_upload_service(
    db:Session,
    uploaded_csv:UploadFile,
    current_company:Company
):
    reset_progress('csv_upload', current_company.slug)
    if not uploaded_csv.filename.endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Cannot process the file, Invalid File!')
    
    contents = await uploaded_csv.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    
    s3_key = f"market-analysis/{current_company.slug}/{uuid4()}.csv"

    try:
        update_csv_file_upload_progress(current_company.slug,15,'Uploading file...')
        s3_client.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=s3_key,
            Body=contents,
            ContentType="text/csv"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
    
    update_csv_file_upload_progress(current_company.slug,25,'File uploaded!')
    process_uploaded_csv.delay(

        str(current_company.id),
        current_company.slug,
        s3_key
    )
    
    return {
        "message": "Upload received, processing started",
    }