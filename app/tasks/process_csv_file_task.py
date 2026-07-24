from app.core.celery_config import celery_app
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.service.etl.extract_service import download_from_s3
from app.agents.csv_analysis_agent import csv_analysis_agent
from app.utils.csv_utils import csv_string_to_json
from app.utils.progress_tracker import update_csv_file_upload_progress,reset_progress
from app.models.company_model import CSVDatas,Company
from app.core.logger import logger
from app.core.database import sessionLocal

import asyncio

@celery_app.task(
    name="process_uploaded_csv_files",
    bind=True,
    max_retries=3,          # retry 3 times on failure
    default_retry_delay=60  # wait 60 seconds between retries
)
def process_uploaded_csv(self,company_id:str,company_slug:str, s3_key:str):
    logger.info(f"CSV task started for {company_slug}") 
    db=None
    try:
        update_csv_file_upload_progress(company_slug,30,'Fetching file...')
        csv_file_content = download_from_s3(s3_key)
        update_csv_file_upload_progress(company_slug,40,'Parsing file...')
        parsed_data = csv_string_to_json(csv_file_content)

        db = sessionLocal()

        update_csv_file_upload_progress(company_slug,50,'Fetching company details...')
        current_company = db.query(Company).filter(Company.id == company_id).first()
        if not current_company:
            logger.error(f"Company not found: {company_id}")
            return
        
        db.execute(text(f'SET search_path TO "{current_company.schema_name}"'))

        update_csv_file_upload_progress(company_slug,55,'Fetching last versions...')
        last_version = (
            db.query(CSVDatas)
            .filter(CSVDatas.company_id == company_id)
            .order_by(CSVDatas.version.desc())
            .first()
        )
        if last_version:
            new_version_number = (last_version.version + 1)
        else:
            new_version_number = 1

        new_version = CSVDatas(
            company_id=company_id,
            version=new_version_number,
            raw_csv_s3_key=s3_key,
            parsed_data=parsed_data,
        )
        previous_data = last_version.parsed_data if last_version else None
        update_csv_file_upload_progress(company_slug,65,'Analysing Data...')
        analysis_result = asyncio.run(
            csv_analysis_agent(
                new_data=parsed_data,
                previous_data=previous_data,
                company_slug=company_slug
            )
        )

        update_csv_file_upload_progress(company_slug,90,'Saving analysed datas...')
        new_version.summary = analysis_result.get("summary")
        new_version.health_score = analysis_result.get("health_score")
        new_version.health_score_reason = analysis_result.get("health_score_reason")
        new_version.growth_areas = analysis_result.get("growth_areas")
        new_version.problem_areas = analysis_result.get("problem_areas")
        new_version.recommendations = analysis_result.get("recommendations")
        new_version.metric_changes = analysis_result.get("metric_changes")
        

        db.add(new_version)
        db.commit()
        update_csv_file_upload_progress(company_slug, 100, 'Analysis complete!') 

    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"process_uploaded_csv failed for {company_slug}: {str(e)}")
        raise self.retry(exc=e)
    finally:
        if db:
            db.close()