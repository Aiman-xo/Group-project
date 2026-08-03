from app.core.celery_config import celery_app
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.service.etl.extract_service import download_from_s3
from app.utils.instagram_comparison_utils import compute_instagram_stats
from app.agents.instagram_comparson_agent import instagram_comparing_agent
from app.service.instagram.load_instagram_data_to_db import load_data_to_instagram_comparison_report,load_data_to_instagram_competitor_profile
from app.models.company_model import Company
from app.models.competitor_model import Competitor
from app.core.logger import logger
from app.core.database import sessionLocal

from app.utils.progress_tracker import (
    update_instagram_comparison_progress,
)

import json
import asyncio

@celery_app.task(
    name="process_instagram_comparison",
    bind=True,
    max_retries=3,          # retry 3 times on failure
    default_retry_delay=60  # wait 60 seconds between retries
)
def process_instagram_comparison(self,current_company_slug:str,competitor_slug:str):
    db = sessionLocal()
    try:
        current_company = db.query(Company).filter(Company.slug == current_company_slug).first()
        if not current_company:
            raise ValueError(f"Company not found for slug {current_company_slug}")
        
        db.execute(text(f'SET search_path TO "{current_company.schema_name}"'))

        competitor = db.query(Competitor).filter(Competitor.slug == competitor_slug).first()
        if not competitor:
            raise ValueError(f"Competitor not found for slug {competitor_slug}")

        update_instagram_comparison_progress(
            str(competitor.id),
            50,
            "Loading Instagram data"
        )
        
        registered_company_file_key = f'social_media/{current_company_slug}/admin/instagram_data.json'
        clean_comp_folder = competitor.company_name.strip().lower().replace(" ", "_")
        competitor_file_key = f'social_media/{current_company_slug}/competitor/{clean_comp_folder}/instagram_data.json'

        update_instagram_comparison_progress(
            str(competitor.id),
            60,
            "Instagram data loaded"
        )

        try:
            registered_company_insta_raw = download_from_s3(registered_company_file_key)
        except Exception as e:
            raise FileNotFoundError(
                f"Missing Instagram data for the registered company ({current_company_slug}) in S3. "
                "Please analyze the registered company's Instagram first."
            ) from e

        try:
            competitor_insta_raw = download_from_s3(competitor_file_key)
        except Exception as e:
            raise FileNotFoundError(
                f"Missing Instagram data for competitor ({competitor_slug}) in S3. "
                "Please analyze this competitor's Instagram first."
            ) from e

        if not registered_company_insta_raw:
            raise ValueError(f"Empty Instagram data file for registered company: {registered_company_file_key}")
            
        if not competitor_insta_raw:
            raise ValueError(f"Empty Instagram data file for competitor: {competitor_file_key}")

        update_instagram_comparison_progress(
            str(competitor.id),
            70,
            "Calculating Instagram statistics"
        )

        try:
            registered_company_insta_data = json.loads(registered_company_insta_raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in S3 file for registered company: {registered_company_file_key}") from e

        try:
            competitor_insta_data = json.loads(competitor_insta_raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in S3 file for competitor: {competitor_file_key}") from e

        registered_company_insta_stats = compute_instagram_stats(registered_company_insta_data)
        competitor_insta_stats = compute_instagram_stats(competitor_insta_data)

        update_instagram_comparison_progress(
            str(competitor.id),
            80,
            "Generating AI comparison"
        )

        result = asyncio.run(instagram_comparing_agent(registered_company_insta_stats=registered_company_insta_stats,competitor_insta_stats=competitor_insta_stats))
        comparison = result.get("comparison", {})
        competitor_highlights = result.get("competitor_highlights", {})
        summary = result.get("summary")
        content_recommendations = result.get("content_recommendations", [])


        update_instagram_comparison_progress(
            str(competitor.id),
            90,
            "AI comparison completed"
        )

        load_data_to_instagram_competitor_profile(db=db,competitor_id=competitor.id,competitor_highlights=competitor_highlights,competitor_compute_data=competitor_insta_stats)
        load_data_to_instagram_comparison_report(db=db,competitor_id=competitor.id,company_id=current_company.id,competitor_name=competitor.company_name,comparison=comparison,summary=summary,content_recommendations=content_recommendations)

        db.commit()

        update_instagram_comparison_progress(
            str(competitor.id),
            100,
            "completed"
        )

        return {'message':'Task completed successfully saved!'}

    except Exception as e:
        if db:
            db.rollback()

        if 'competitor' in locals() and competitor:
            update_instagram_comparison_progress(
                str(competitor.id),
                -1,
                "failed"
            )

        logger.error(
            f"process_instagram_comparison failed "
            f"for {current_company_slug}: {str(e)}"
        )

        raise self.retry(exc=e)
    finally:
        if db:
            db.close() 