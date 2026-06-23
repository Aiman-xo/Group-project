from fastapi import APIRouter

from app.schemas.website_url_schema import (
    CompetitorSearchRequest
)

from app.service.website_url_service import (
    discover_competitors
)


router = APIRouter(
    prefix="/competitors",
    tags=["Competitor Discovery"]
)


@router.post("/discover")
async def competitor_search(
    payload: CompetitorSearchRequest
):
    return await discover_competitors(
        industry=payload.industry,
        country=payload.country,
        state=payload.state,
        district=payload.district
    )