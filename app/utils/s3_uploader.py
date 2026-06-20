import os
import boto3
from io import StringIO
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

class S3Uploader:
    def __init__(self):
        self.bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "saas-comparison-engine-data-lake")
        
        # Pull keys from your .env
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        # If real keys aren't added yet, default to safe simulation mode
        if self.access_key and "YOUR_" not in self.access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=os.getenv("AWS_REGION", "ap-south-1")
            )
            self.is_mock = False
        else:
            self.is_mock = True

    def upload_string_to_s3(self, raw_text_data: str, s3_target_key: str) -> bool:
        """Streams text data directly into memory and pushes it up to an S3 path."""
        if self.is_mock:
            print(f"  [SIMULATION] Pushed direct string ──> S3://{self.bucket_name}/{s3_target_key}")
            return True

        try:
            # Convert our text string data directly into an in-memory file stream
            text_stream = StringIO(raw_text_data)
            
            # Put the object into the structured S3 partition
            self.s3_client.put_object(
                Body=text_stream.getvalue(),
                Bucket=self.bucket_name,
                Key=s3_target_key,
                ContentType='text/plain'
            )
            print(f"  [✓] Live S3 Sync Complete: s3://{self.bucket_name}/{s3_target_key}")
            return True
        except NoCredentialsError:
            print("  [X] AWS Credentials validation failed.")
            return False
        except Exception as e:
            print(f"  [X] S3 Storage Upload Failure: {e}")
            return False