
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.service.google_ads_service import GoogleAdsService
from app.schemas.google_ads_schema import GoogleAdItem

router = APIRouter(
    prefix="/api/google-ads",
    tags=["Google Ads Intelligence"]
)

ads_service = GoogleAdsService()


@router.get("/analyze", response_model=List[GoogleAdItem])
async def get_and_analyze_ads(
    search_term: str = Query(..., description="Company domain or brand name (e.g. scaler.com, bridgeon.in)")
):
    """
    Fetches active Google Ads / search presence for a domain and analyzes
    rendering instructions (iframes, youtube embeds, images) for the frontend.
    Runs in-memory without S3/DB overhead.
    """
    try:
        # Fetches ads and automatically performs UI render analysis
        ads = ads_service.fetch_active_ads(search_term=search_term)
        return ads

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to analyze Google Ads for '{search_term}': {str(e)}"
        )