from fastapi import APIRouter,UploadFile,File,Depends
from sqlalchemy.orm import Session
from app.core.multitenancy import get_authorized_tenant_db
from app.service.company_service import check_company_url
from app.core.multitenancy import get_current_company
from app.service.company_service import csv_upload_service
from app.models.company_model import Company
from app.schemas.csv_upload_schema import CsvUploadResponse


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

# CSV upload route
@router.post('/upload/csv',response_model=CsvUploadResponse)
async def upload_csv(
    uploaded_csv:UploadFile = File(...), 
    db:Session = Depends(get_authorized_tenant_db),
    current_company:Company=Depends(get_current_company)
):
    return await csv_upload_service(uploaded_csv=uploaded_csv,current_company=current_company,db=db)