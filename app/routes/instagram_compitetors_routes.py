from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.core.multitenancy import (
    get_current_company,
    get_authorized_tenant_db,
)
from app.models.competetor_analyser import CompetetorAnalyser
from app.models.competitor_model import Competitor
from app.service.instagram_service import InstagramService


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

    return {
        "success": True,
        "message": "Competitor Instagram data collected successfully",
    }