from app.models.competitor_model import InstagramCompetitorProfile
from app.models.competetor_analyser import InstagramComparisonReport
from sqlalchemy.orm import Session
from app.core.logger import logger
from sqlalchemy.exc import SQLAlchemyError


def load_data_to_instagram_competitor_profile(db:Session,competitor_id:str,competitor_highlights:dict,competitor_compute_data:dict):
    try:
        latest = db.query(InstagramCompetitorProfile).filter(
            InstagramCompetitorProfile.competitor_id == competitor_id
        ).order_by(InstagramCompetitorProfile.version.desc()).first()

        db.query(InstagramCompetitorProfile).filter(
            InstagramCompetitorProfile.competitor_id == competitor_id,
            InstagramCompetitorProfile.is_latest == True
        ).update({"is_latest": False})

        next_version = (latest.version + 1) if latest else 1

        new_data = InstagramCompetitorProfile(
            competitor_id=competitor_id,
            version=next_version,
            is_latest=True,

            strongest_content_type = competitor_highlights.get("strongest_content_type"),
            standout_themes = competitor_highlights.get("standout_themes"),
            top_post_insight = competitor_highlights.get("top_post_insight"),
            notable_traits = competitor_highlights.get("notable_traits"),

            instagram_id = competitor_compute_data.get("instagram_id"),
            username = competitor_compute_data.get("username"),
            full_name = competitor_compute_data.get("full_name"),
            biography = competitor_compute_data.get("biography"),
            followers_count = competitor_compute_data.get("followers_count"),
            follows_count = competitor_compute_data.get("follows_count"),
            posts_count = competitor_compute_data.get("posts_count"),
            verified = competitor_compute_data.get("verified"),
            is_business_account = competitor_compute_data.get("is_business_account"),
            business_category_name = competitor_compute_data.get("business_category_name"),
            external_urls = competitor_compute_data.get("external_urls"),

            analyzed_posts_count = competitor_compute_data.get("analyzed_posts_count"),
            total_likes = competitor_compute_data.get("total_likes"),
            total_comments = competitor_compute_data.get("total_comments"),
            total_video_views = competitor_compute_data.get("total_video_views"),
            average_likes = competitor_compute_data.get("average_likes"),
            average_comments = competitor_compute_data.get("average_comments"),
            average_video_views = competitor_compute_data.get("average_video_views"),
            engagement_rate = competitor_compute_data.get("engagement_rate"),
            
            content_type_performance = competitor_compute_data.get("content_type_performance"),
            posting_frequency_per_week = competitor_compute_data.get("posting_frequency_per_week"),
            has_external_links = competitor_compute_data.get("has_external_links"),
            avg_hashtags_per_post = competitor_compute_data.get("avg_hashtags_per_post"),
            avg_caption_length = competitor_compute_data.get("avg_caption_length"),

            latest_posts = competitor_compute_data.get("latest_posts"),
            top_hashtags = competitor_compute_data.get("top_hashtags"),
            top_mentions = competitor_compute_data.get("top_mentions"),
            content_type_stats = competitor_compute_data.get("content_type_stats"),
            top_post = competitor_compute_data.get("top_post"),
            top_video = competitor_compute_data.get("top_video")
        )
        db.add(new_data)
        db.flush()
        return new_data
    except SQLAlchemyError as se:
        db.rollback()
        logger.error(f"Database error saving Instagram competitor profile for {competitor_id}: {str(se)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error saving Instagram competitor profile for {competitor_id}: {str(e)}")
        raise

def load_data_to_instagram_comparison_report(db:Session,competitor_id:str,company_id:str,competitor_name:str,comparison:dict,summary:str,content_recommendations:list):
    try:
        db.query(InstagramComparisonReport).filter(
            InstagramComparisonReport.competitor_id == competitor_id,
            InstagramComparisonReport.is_latest == True
        ).update({"is_latest": False})

        latest = db.query(InstagramComparisonReport).filter(
            InstagramComparisonReport.competitor_id == competitor_id
        ).order_by(InstagramComparisonReport.version.desc()).first()

        next_version = (latest.version + 1) if latest else 1

        new_data = InstagramComparisonReport(
            competitor_id=competitor_id,
            company_id=company_id,
            competitor_name=competitor_name,
            summary=summary,
            engagement_gap=comparison.get("engagement_gap"),
            content_strategy_gap=comparison.get("content_strategy_gap"),
            audience_gap=comparison.get("audience_gap"),
            posting_cadence_gap=comparison.get("posting_cadence_gap"),
            positioning_summary=comparison.get("positioning_summary"),
            recommendations=comparison.get("recommendations"),
            content_recommendations=content_recommendations, 
            version=next_version,
            is_latest=True,
        )
        db.add(new_data)
        db.flush()
        return new_data
    
    except SQLAlchemyError as se:
        db.rollback()
        logger.error(f"Database error saving Instagram comparison report for {competitor_id}: {str(se)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error saving Instagram comparison report for {competitor_id}: {str(e)}")
        raise


# def update_data_to_instagram_analyses_model(computed_data:dict):
#     return computed_data