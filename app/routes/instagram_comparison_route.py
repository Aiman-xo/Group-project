from fastapi import APIRouter,Depends
from app.core.multitenancy import get_authorized_tenant_db,get_current_company
from app.service.instagram.instagram_comparison_service import instagram_comparison_service
from app.models.company_model import Company
from sqlalchemy.orm import Session
from uuid import UUID


router = APIRouter(prefix='/instagram-comparison',tags=["Instagram Comparison"])

@router.post('/{competitor_id}')
def instagram_comparison_route(competitor_id:UUID,db:Session = Depends(get_authorized_tenant_db), current_company:Company = Depends(get_current_company)):
    return instagram_comparison_service(competitor_id=competitor_id,db=db,current_company=current_company)