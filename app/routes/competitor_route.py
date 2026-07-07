from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.models.company_model import Company
from app.schemas.competitor_return_schema import CompetitorReturnResponse
# from app.core.database import get_tenant_db
from app.core.multitenancy import get_authorized_tenant_db,get_current_company
from app.service.competitor_return_service import get_competitor_datas

router = APIRouter(prefix='/competitors',tags=["competitors_datas"])

@router.get('/competitor_details',response_model=CompetitorReturnResponse)
async def get_competitors(
    page: int = 1,
    limit : int = 10,
    db:Session = Depends(get_authorized_tenant_db),
    # current_company : Company = Depends(get_current_company),

):
    return await get_competitor_datas(db=db,page=page,limit=limit)