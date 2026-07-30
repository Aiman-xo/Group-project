from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.core.multitenancy import (
    get_current_company,
    get_authorized_tenant_db,
)
from app.models.competetor_analyser import CompetetorAnalyser,InstagramComparisonReport
from app.models.competitor_model import Competitor,InstagramCompetitorProfile
from app.models.company_model import InstagramAnalysis
from app.service.instagram.instagram_service import InstagramService
from app.core.multitenancy import get_current_company
from app.tasks.instagram_comparison_task import process_instagram_comparison



router = APIRouter(
    prefix="/competitors",
    tags=["Competitor Instagram"]
)

instagram_service = InstagramService()


class InstagramURLRequest(BaseModel):
    instagram_url: HttpUrl


# =========================================================
# Helper - Get competitor
# =========================================================

def get_competitor_or_404(
    db: Session,
    competitor_id: str,
):
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.id == competitor_id,
            Competitor.is_active.is_(True),
        )
        .first()
    )

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found",
        )

    return competitor


# =========================================================
# Helper - Get latest competitor analysis
# =========================================================

def get_latest_competitor_analysis_or_404(
    db: Session,
    competitor_id,
):
    analysis = (
        db.query(CompetetorAnalyser)
        .filter(
            CompetetorAnalyser.competitor_id == competitor_id,
            CompetetorAnalyser.is_latest.is_(True),
        )
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor analysis not found",
        )

    return analysis


# =========================================================
# Add / Edit Instagram URL
# =========================================================

@router.put("/{competitor_id}/instagram-url")
def update_competitor_instagram_url(
    competitor_id: str,
    payload: InstagramURLRequest,
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    competitor = get_competitor_or_404(
        db,
        competitor_id,
    )

    analysis = get_latest_competitor_analysis_or_404(
        db,
        competitor.id,
    )

    instagram_url = str(payload.instagram_url)

    analysis.instagram = instagram_url

    db.commit()

    return {
        "success": True,
        "message": "Competitor Instagram URL updated successfully",
        "instagram_url": instagram_url,
    }


# =========================================================
# Connect / Analyze Instagram
# =========================================================

@router.post("/{competitor_id}/instagram/connect")
def connect_competitor_instagram(
    competitor_id: str,
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    competitor = get_competitor_or_404(
        db,
        competitor_id,
    )

    analysis = get_latest_competitor_analysis_or_404(
        db,
        competitor.id,
    )

    if not analysis.instagram:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competitor Instagram URL not found",
        )
 
    success = instagram_service.process_instagram(
        db=db,
        company_id=current_company.id,
        company_slug=str(current_company.slug),
        company_name=competitor.company_name,
        instagram_url=analysis.instagram,
        is_competitor=True,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to fetch competitor Instagram data",
        )

    process_instagram_comparison.delay(
        str(current_company.slug),
        str(competitor.slug),
    )

    return {
        "success": True,
        "message": "Competitor Instagram data collected successfully",
    }


# @router.get("/{competitor_id}/instagram/analysis")
# def get_competitor_instagram_analysis(
#     competitor_id: str,
#     db: Session = Depends(get_authorized_tenant_db),
#     current_company=Depends(get_current_company),
# ):
#     # Make sure competitor exists and belongs to the
#     # currently authorized tenant.
#     competitor = get_competitor_or_404(
#         db,
#         competitor_id,
#     )

#     analysis = get_latest_competitor_analysis_or_404(
#         db,
#         competitor.id,
#     )

#     profile = (
#         db.query(InstagramCompetitorProfile)
#         .filter(
#             InstagramCompetitorProfile.competitor_id == competitor.id,
#             InstagramCompetitorProfile.is_latest.is_(True),
#         )
#         .first()
#     )

#     comparison = (
#         db.query(InstagramComparisonReport)
#         .filter(
#             InstagramComparisonReport.competitor_id == competitor.id,
#             InstagramComparisonReport.company_id == current_company.id,
#             InstagramComparisonReport.is_latest.is_(True),
#         )
#         .first()
#     )

#     # No Instagram analysis has been generated yet.
#     if not profile or not comparison:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Instagram analysis not found",
#         )

#     return {
#         "success": True,
#         "data": {
#             "competitor": {
#                 "id": str(competitor.id),
#                 "name": competitor.company_name,
#                 "slug": competitor.slug,
#                 "instagram_url": analysis.instagram,

#                 "profile": {
#                     "instagram_id": profile.instagram_id,
#                     "username": profile.username,
#                     "full_name": profile.full_name,
#                     "biography": profile.biography,

#                     "verified": profile.verified,
#                     "is_business_account": profile.is_business_account,
#                     "business_category_name": profile.business_category_name,

#                     "followers_count": profile.followers_count,
#                     "following_count": profile.follows_count,
#                     "posts_count": profile.posts_count,

#                     "external_urls": profile.external_urls,
#                 },

#                 "performance": {
#                     "posts_analyzed": profile.analyzed_posts_count,

#                     "engagement_rate": (
#                         float(profile.engagement_rate)
#                         if profile.engagement_rate is not None
#                         else None
#                     ),

#                     "totals": {
#                         "likes": profile.total_likes,
#                         "comments": profile.total_comments,
#                         "video_views": profile.total_video_views,
#                     },

#                     "averages": {
#                         "likes": profile.average_likes,
#                         "comments": profile.average_comments,
#                         "video_views": profile.average_video_views,
#                     },

#                     "content_types": profile.content_type_stats,
#                 },

#                 "content": {
#                     "top_hashtags": profile.top_hashtags,
#                     "top_mentions": profile.top_mentions,
#                     "top_post": profile.top_post,
#                     "top_video": profile.top_video,
#                 },

#                 "ai_highlights": {
#                     "strongest_content_type": profile.strongest_content_type,
#                     "standout_themes": profile.standout_themes,
#                     "top_post_insight": profile.top_post_insight,
#                     "notable_traits": profile.notable_traits,
#                 },
#             },

#             "comparison": {
#                 "summary": {
#                     "competitor_name": comparison.competitor_name,
#                     "engagement_gap": comparison.engagement_gap,
#                     "content_strategy_gap": comparison.content_strategy_gap,
#                     "audience_gap": comparison.audience_gap,
#                     "positioning_summary": comparison.positioning_summary,
#                 },

#                 "recommendations": comparison.recommendations,
#             },

#             "analysis": {
#                 "version": profile.version,
#                 "last_analyzed_at": profile.last_analyzed_at,
#             },
#         },
#     }
@router.get("/{competitor_id}/instagram/analysis")
def get_competitor_instagram_analysis(
    competitor_id: str,
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    # Make sure competitor exists and belongs to the
    # currently authorized tenant.
    competitor = get_competitor_or_404(
        db,
        competitor_id,
    )

    analysis = get_latest_competitor_analysis_or_404(
        db,
        competitor.id,
    )

    profile = (
        db.query(InstagramCompetitorProfile)
        .filter(
            InstagramCompetitorProfile.competitor_id == competitor.id,
            InstagramCompetitorProfile.is_latest.is_(True),
        )
        .first()
    )

    comparison = (
        db.query(InstagramComparisonReport)
        .filter(
            InstagramComparisonReport.competitor_id == competitor.id,
            InstagramComparisonReport.company_id == current_company.id,
            InstagramComparisonReport.is_latest.is_(True),
        )
        .first()
    )

    # Company's own Instagram data (saved separately when they
    # connected Instagram at registration / from their insights tab).
    company_profile = (
        db.query(InstagramAnalysis)
        .filter(
            InstagramAnalysis.company_id == current_company.id,
            InstagramAnalysis.is_latest.is_(True),
        )
        .first()
    )

    # No Instagram analysis has been generated yet.
    if not profile or not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram analysis not found",
        )

    def serialize_profile(p):
        if not p:
            return None
        return {
            "instagram_id": p.instagram_id,
            "username": p.username,
            "full_name": p.full_name,
            "biography": p.biography,

            "verified": p.verified,
            "is_business_account": p.is_business_account,
            "business_category_name": p.business_category_name,

            "followers_count": p.followers_count,
            "following_count": p.follows_count,
            "posts_count": p.posts_count,

            "external_urls": p.external_urls,

            "performance": {
                "posts_analyzed": p.analyzed_posts_count,
                "engagement_rate": (
                    float(p.engagement_rate)
                    if p.engagement_rate is not None
                    else None
                ),
                "totals": {
                    "likes": p.total_likes,
                    "comments": p.total_comments,
                    "video_views": p.total_video_views,
                },
                "averages": {
                    "likes": p.average_likes,
                    "comments": p.average_comments,
                    "video_views": p.average_video_views,
                },
                "content_types": p.content_type_stats,
            },

            "content": {
                "top_hashtags": p.top_hashtags,
                "top_mentions": p.top_mentions,
                "top_post": p.top_post,
                "top_video": p.top_video,
            },
        }

    def to_float(v):
        return float(v) if v is not None else None

    # Structured numeric metrics for charts — no LLM text parsing needed.
    metrics = {
        "followers_count": {
            "company": company_profile.followers_count if company_profile else None,
            "competitor": profile.followers_count,
        },
        "following_count": {
            "company": company_profile.follows_count if company_profile else None,
            "competitor": profile.follows_count,
        },
        "posts_count": {
            "company": company_profile.posts_count if company_profile else None,
            "competitor": profile.posts_count,
        },
        "engagement_rate": {
            "company": to_float(company_profile.engagement_rate) if company_profile else None,
            "competitor": to_float(profile.engagement_rate),
        },
        "average_likes": {
            "company": company_profile.average_likes if company_profile else None,
            "competitor": profile.average_likes,
        },
        "average_comments": {
            "company": company_profile.average_comments if company_profile else None,
            "competitor": profile.average_comments,
        },
        "average_video_views": {
            "company": company_profile.average_video_views if company_profile else None,
            "competitor": profile.average_video_views,
        },
        "total_likes": {
            "company": company_profile.total_likes if company_profile else None,
            "competitor": profile.total_likes,
        },
        "total_comments": {
            "company": company_profile.total_comments if company_profile else None,
            "competitor": profile.total_comments,
        },
    }

    return {
        "success": True,
        "data": {
            "competitor": {
                "id": str(competitor.id),
                "name": competitor.company_name,
                "slug": competitor.slug,
                "instagram_url": analysis.instagram,
                "profile": serialize_profile(profile),
                "ai_highlights": {
                    "strongest_content_type": profile.strongest_content_type,
                    "standout_themes": profile.standout_themes,
                    "top_post_insight": profile.top_post_insight,
                    "notable_traits": profile.notable_traits,
                },
                "version": profile.version,
                "last_analyzed_at": profile.last_analyzed_at,
            },

            "company": {
                "id": str(current_company.id),
                "profile": serialize_profile(company_profile),
                "has_instagram_connected": company_profile is not None,
                "last_analyzed_at": company_profile.last_analyzed_at if company_profile else None,
            },

            "comparison": {
                "metrics": metrics,
                "narrative": {
                    "engagement_gap": comparison.engagement_gap,
                    "content_strategy_gap": comparison.content_strategy_gap,
                    "audience_gap": comparison.audience_gap,
                    "positioning_summary": comparison.positioning_summary,
                },
                "recommendations": comparison.recommendations,
            },
        },
    }