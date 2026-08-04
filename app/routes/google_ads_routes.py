
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models.competitor_model import Competitor
from app.service.google_ads_service import GoogleAdsService
from app.core.multitenancy import get_authorized_tenant_db  

router = APIRouter(
    prefix="/google-ads",
    tags=["Google Ads Intelligence"]
)

ads_service = GoogleAdsService()


@router.get("/analyze/{competitor_id}", response_model=Dict[str, Any])
async def get_and_analyze_ads(
    competitor_id: UUID = Path(..., description="UUID of the competitor"),
    # search_term: str = Query(..., description="Company domain or brand name (e.g. scaler.com, bridgeon.in)"),
    db: Session = Depends(get_authorized_tenant_db)
):
    """
    Checks the DB for existing Google Ads report for the competitor.
    If missing, fetches active Google Ads via SerpApi, computes frontend render specs,
    runs AI strategy analysis via GoogleAdsAgent, and persists the report to DB.
    """
    competitor = (
        db.query(Competitor)
        .filter(Competitor.id == competitor_id)
        .first()
    )

    if competitor is None:
        raise HTTPException(
            status_code=404,
            detail="Competitor not found."
        )

    try:
        report = ads_service.get_or_analyze_ads(
            competitor_id=competitor.id,
            company_id=None,
            competitor_name=competitor.company_name,
            search_term=(
                competitor.website_url
                or competitor.company_name
            ),
            db=db,
        )

        return report

    except Exception as e:
        print(f"[GOOGLE ADS ROUTE ERROR] {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to analyze Google Ads."
        )