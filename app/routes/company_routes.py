from fastapi import APIRouter
from app.service.company_service import check_company_url

router = APIRouter(
    prefix="/company",
    tags=["company"]
)

@router.get("/check-url")
async def check_url(url: str):
    return await check_company_url(url)