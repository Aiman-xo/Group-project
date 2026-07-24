from typing import Optional
from app.core.celery_config import celery_app
# from app.utils.s3_filepath_extractor import extract_s3_metadata
from app.service.etl.transform_service import transform
from app.core.logger import logger
# from app.core.config import REDIS_URL
from app.core.database import sessionLocal
from app.models.company_model import Company
from app.models.competitor_model import Competitor
from sqlalchemy import text
from app.service.etl.load_into_db_service import load_competitor_data_to_db,load_profile_data_to_db
from app.service.etl.extract_service import extract_content_from_file
from app.service.compare_service import run_compare_agent
from app.utils.progress_tracker import update_etl_progress
from sqlalchemy.exc import SQLAlchemyError

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
def process_etl_file(self, company_slug: str, folder: str, file_keys: list, competitor_slug:Optional[str]):
    """
    Celery task that runs the ETL pipeline.
    Called when SQS message arrives 
    """
    db = None
    competitor = None
    competitor_id = None 
    try:
        logger.info(f"Starting ETL for {company_slug}/{folder} with {len(file_keys)} files")

        # ── Step 1: Extract & combine all files ─────────────────────────
        combined_raw_text = ""
        for key in file_keys:
            logger.info(f"Extracting: {key}")
            content = extract_content_from_file(key)  # ← handles both .json and .txt
            if content:
                combined_raw_text += f"\n\n--- Source: {key} ---\n{content}"

        update_etl_progress(company_slug,60,'Extraction Completed')
         # ── Step 2: Transform once on combined text ──────────────────────
        update_etl_progress(company_slug,60,'Transforming Datas...')
        transformed_data = asyncio.run(
            transform({
                "raw_data": combined_raw_text,
                "source_file": None
            })
        )
        update_etl_progress(company_slug,70,'Transforming Datas Completed.')

        if transformed_data is None:
            logger.error(f"Transform returned None for {company_slug}. Aborting.")
            return
        
        db = sessionLocal()
        update_etl_progress(company_slug,75,'Checking company datas...')
        current_company = db.query(Company).filter(Company.slug == company_slug).first()

        if not current_company:
            logger.error(f'could not able to fetch the company try again!')
            return
        
        update_etl_progress(company_slug,80,'Fetching company details...')
        db.execute(text(f'SET search_path TO "{current_company.schema_name}"'))

        update_etl_progress(company_slug,90,'Savind Datas...')
        if folder == "admin":
            update_etl_progress(company_slug,95,'Creating Versions...')
            response = load_profile_data_to_db(
                llm_output=transformed_data,
                db=db,
                company_id=current_company.id,
            )
            logger.info(f"ETL task completed for: {company_slug}")
            logger.info(response)
            update_etl_progress(company_slug,100,'ETL process completed.')

        elif folder == "competitor":
            competitor = db.query(Competitor).filter(Competitor.slug == competitor_slug).first()
            if not competitor:
                logger.error(f"Competitor with slug '{competitor_slug}' not found in DB. Aborting ETL.")
                return
            
            competitor_id = competitor.id 

            update_etl_progress(company_slug,95,'Creating Versions...')
            response = load_competitor_data_to_db(
                llm_output=transformed_data,
                db=db,
                competitor_id=competitor_id
            )
            logger.info(f"ETL task completed for competitor: {competitor_slug}")

            db.execute(text(f'SET search_path TO "{current_company.schema_name}"'))

            compare_response = asyncio.run(run_compare_agent(competitor_id=competitor_id, company_id=current_company.id, db=db))
            logger.info(f"compare agent run status: {compare_response} ===============>>")
            update_etl_progress(company_slug,100,'ETL process completed.')

        else:
            logger.error(f"Unknown folder type: {folder}")
    
    except SQLAlchemyError as se:
        if db:
            db.rollback()
        logger.error(f"Database error occurred while saving comparison data for competitor {competitor_id}: {str(se)}")
        return None
        
    except KeyError as ke:
        if db:
            db.rollback()
        logger.error(f"Missing required key in transformed_data dictionary: {str(ke)}")
        return None
    
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"process_company_files failed for {company_slug}: {str(e)}")
        raise self.retry(exc=e)
        
    finally:
        if db:
            db.close()