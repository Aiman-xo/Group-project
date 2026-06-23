from app.core.celery_config import celery_app
# from app.utils.s3_filepath_extractor import extract_s3_metadata
from app.service.etl.transform_service import transform
from app.core.logger import logger
# from app.core.config import REDIS_URL
from app.core.database import sessionLocal
from app.models.company_model import Company
from sqlalchemy import text
from app.service.etl.load_into_db_service import load_competitor_data_to_db,load_profile_data_to_db
from app.service.etl.extract_service import extract_content_from_file
import asyncio
import json
# import redis as redis_client



# ────────────────────────────────────────────────────────────────────────
# TASK 2 — Called once all 3 files are collected

@celery_app.task(
    name="etl.process_company_files",
    bind=True,
    max_retries=3,          # retry 3 times on failure
    default_retry_delay=60  # wait 60 seconds between retries
)
def process_etl_file(self, company_slug: str, folder: str, file_keys: list):
    """
    Celery task that runs the ETL pipeline.
    Called when SQS message arrives 

    """
    try:
        logger.info(f"Starting ETL for {company_slug}/{folder} with {len(file_keys)} files")

        # ── Step 1: Extract & combine all files ─────────────────────────
        combined_raw_text = ""
        for key in file_keys:
            logger.info(f"Extracting: {key}")
            content = extract_content_from_file(key)  # ← handles both .json and .txt
            if content:
                combined_raw_text += f"\n\n--- Source: {key} ---\n{content}"

         # ── Step 2: Transform once on combined text ──────────────────────
        transformed_data = asyncio.run(
            transform({
                "raw_data": combined_raw_text,
                "source_file": None
            })
        )

        if transformed_data is None:
            logger.error(f"Transform returned None for {company_slug}. Aborting.")
            return
        
        db = sessionLocal()
        try:

            current_company = db.query(Company).filter(Company.slug == company_slug).first()

            if not current_company:
                logger.error(f'could not able to fetch the company try again!')
                return
            
            db.execute(text(f'SET search_path TO "{current_company.schema_name}"'))

            if folder == "admin":
                response = load_profile_data_to_db(
                    llm_output=transformed_data,
                    db=db,
                    company_id=current_company.id,
                )
                logger.info(f"ETL task completed for: {company_slug}")

                print(response)

            elif folder == "competitor":
                pass
                # =================================================================================
                # Need to write if the folder is copetitor code later.
                # =================================================================================
            else:
                logger.error(f"Unknown folder type: {folder}")
    
        finally:
                db.close()

    except Exception as e:
        logger.error(f"process_company_files failed for {company_slug}: {str(e)}")
        raise self.retry(exc=e)