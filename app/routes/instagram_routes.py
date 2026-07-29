from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.multitenancy import (
    get_current_company,
    get_authorized_tenant_db,
)
from app.models.company_model import ProfileDataAnalyser
from app.schemas.instagram_schema import InstagramUrlUpdate
from app.service.instagram.instagram_service import InstagramService


router = APIRouter(
    prefix="/instagram",
    tags=["Instagram"]
)

instagram_service = InstagramService()


# =========================================================
# Check Instagram URL
# =========================================================

@router.get("/connection-status")
def check_instagram_connection(
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):

    profile = (
        db.query(ProfileDataAnalyser)
        .filter(
            ProfileDataAnalyser.company_id == current_company.id,
            ProfileDataAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    if not profile.instagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company Instagram URL not found"
        )

    return {
        "connected": True,
        "instagram_url": profile.instagram
    }


# =========================================================
# Add / Edit Instagram URL
# =========================================================

@router.put("/instagram-url")
def update_instagram_profile_url(
    payload: InstagramUrlUpdate,
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    profile = (
        db.query(ProfileDataAnalyser)
        .filter(
            ProfileDataAnalyser.company_id == current_company.id,
            ProfileDataAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    profile.instagram = payload.instagram_url

    db.commit()

    return {
        "instagram_url": payload.instagram_url
    }

# =========================================================
# Connect / Analyze Instagram
# =========================================================

@router.post("/connect")
def connect_instagram(
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    profile = (
        db.query(ProfileDataAnalyser)
        .filter(
            ProfileDataAnalyser.company_id == current_company.id,
            ProfileDataAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    if not profile.instagram:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram URL not found"
        )

    # success = instagram_service.process_instagram(
    #     company_slug=str(current_company.slug),
    #     company_name=current_company.company_name,
    #     instagram_url=profile.instagram,
    #     is_competitor=False,
    # )
    success = instagram_service.process_instagram(
        db=db,
        company_id=current_company.id,
        company_slug=str(current_company.slug),
        company_name=current_company.company_name,
        instagram_url=profile.instagram,
        is_competitor=False,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to fetch Instagram data"
        )

    return {
        "success": True,
        "message": "Instagram data collected successfully"
    }

@router.get("/analysis")
def get_instagram_analysis(
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    analysis = (
        db.query(InstagramAnalysis)
        .filter(
            InstagramAnalysis.company_id == current_company.id,
            InstagramAnalysis.is_latest.is_(True),
        )
        .order_by(InstagramAnalysis.created_at.desc())
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram analysis not found"
        )

    return {
        "success": True,
        "data": {
            "id": analysis.id,

            # Profile
            "instagram_id": analysis.instagram_id,
            "username": analysis.username,
            "full_name": analysis.full_name,
            "biography": analysis.biography,
            "followers_count": analysis.followers_count,
            "follows_count": analysis.follows_count,
            "posts_count": analysis.posts_count,
            "verified": analysis.verified,
            "is_business_account": analysis.is_business_account,
            "business_category_name": analysis.business_category_name,
            "external_urls": analysis.external_urls,

            # Posts summary
            "analyzed_posts_count": analysis.analyzed_posts_count,
            "total_likes": analysis.total_likes,
            "total_comments": analysis.total_comments,
            "total_video_views": analysis.total_video_views,

            # Average engagement
            "average_likes": analysis.average_likes,
            "average_comments": analysis.average_comments,
            "average_video_views": analysis.average_video_views,
            "engagement_rate": (
                float(analysis.engagement_rate)
                if analysis.engagement_rate is not None
                else None
            ),

            # Analysis
            "content_type_stats": analysis.content_type_stats,
            "top_hashtags": analysis.top_hashtags,
            "top_mentions": analysis.top_mentions,

            # Best content
            "top_post": analysis.top_post,
            "top_video": analysis.top_video,

            # Posts
            "latest_posts": analysis.latest_posts,

            # Metadata
            "version": analysis.version,
            "last_analyzed_at": analysis.last_analyzed_at,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
        }
    }