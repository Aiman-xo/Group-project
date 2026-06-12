from fastapi import APIRouter ,Depends
from app.service.company_service import check_company_url
from app.core.multitenancy import get_current_company

router = APIRouter(
    prefix="/company",
    tags=["company"]
)

@router.get("/check-url")
async def check_url(url: str):
    return await check_company_url(url)

@router.get("/me")
async def me(
    company = Depends(get_current_company)
):
    return {
        "id": str(company.id),
        "company_name": company.company_name,
        "slug": company.slug,
        "schema_name": company.schema_name
    }