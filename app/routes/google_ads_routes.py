# from fastapi import APIRouter, HTTPException, Query
# from typing import List, Optional
# from app.service.google_ads_service import GoogleAdsService
# from app.schemas.google_ads_schema import FrontendAdAnalysis

# router = APIRouter(
#     prefix="/api/google-ads",
#     tags=["Google Ads Intelligence"]
# )

# ads_service = GoogleAdsService()


# @router.get("/analyze", response_model=List[FrontendAdAnalysis])
# async def get_and_analyze_ads(
#     search_term: str = Query(..., description="Company domain or brand name (e.g. scaler.com, bridgeon.in)")
# ):
#     """
#     Fetches active Google Ads / search presence for a domain and analyzes
#     rendering instructions (iframes, youtube embeds, images) for the frontend.
#     Runs in-memory without S3/DB overhead.
#     """
#     try:
#         # 1. Fetch ads/footprints using SerpApi
#         raw_ads = ads_service.fetch_active_ads(search_term=search_term)
        
#         if not raw_ads:
#             return []

#         # 2. Analyze each ad item for frontend rendering strategy
#         analyzed_results = []
#         for ad in raw_ads:
#             # Convert Pydantic item to dict if needed
#             ad_dict = ad.model_dump() if hasattr(ad, "model_dump") else ad
#             analysis = ads_service.analyze_ad_for_frontend(ad_dict)
#             analyzed_results.append(analysis)

#         return analyzed_results

#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Failed to analyze Google Ads for '{search_term}': {str(e)}"
#         )

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