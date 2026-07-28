from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.competetor_analyser import CompetetorAnalyser
from app.models.competitor_model import Competitor
from app.service.instagram_service import InstagramService
from app.core.multitenancy import get_current_company


router = APIRouter(
    prefix="/competitors",
    tags=["Instagram Analysis"]
)

instagram_service = InstagramService()


class InstagramURLRequest(BaseModel):
    instagram_url: HttpUrl


# =========================================================
# 1. Analyze using Instagram URL already stored
# =========================================================

@router.post("/{slug}/instagram/analyze")
def analyze_competitor_instagram(
    slug: str,
    db: Session = Depends(get_db),
    current_company=Depends(get_current_company),
):

    # Find competitor using slug
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.slug == slug,
            Competitor.is_active.is_(True)
        )
        .first()
    )

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    # Get latest analysis for this competitor
    analysis = (
        db.query(CompetetorAnalyser)
        .filter(
            CompetetorAnalyser.competitor_id == competitor.id,
            CompetetorAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor analysis not found"
        )

    # Instagram URL not discovered during website analysis
    if not analysis.instagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram URL not found"
        )

    success = instagram_service.process_instagram(
        company_id=str(current_company.id),
        company_name=competitor.company_name,
        instagram_url=analysis.instagram
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Instagram analysis failed"
        )

    return {
        "success": True,
        "message": "Instagram analysis completed"
    }


# =========================================================
# 2. Manually provide Instagram URL and analyze
# =========================================================

@router.post("/{slug}/instagram/analyze-manual")
def analyze_competitor_instagram_manual(
    slug: str,
    payload: InstagramURLRequest,
    db: Session = Depends(get_db),
    current_company=Depends(get_current_company),
):

    # Find competitor using slug
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.slug == slug,
            Competitor.is_active.is_(True)
        )
        .first()
    )

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    # Get latest competitor analysis
    analysis = (
        db.query(CompetetorAnalyser)
        .filter(
            CompetetorAnalyser.competitor_id == competitor.id,
            CompetetorAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor analysis not found"
        )

    instagram_url = str(payload.instagram_url)

    # Save manually provided Instagram URL
    analysis.instagram = instagram_url

    db.commit()
    db.refresh(analysis)

    # Run Instagram analysis
    success = instagram_service.process_instagram(
        company_id=str(current_company.id),
        company_name=competitor.company_name,
        instagram_url=instagram_url
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Instagram analysis failed"
        )

    return {
        "success": True,
        "message": "Instagram URL saved and analysis completed"
    }