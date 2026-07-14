from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from app.schemas.analysis_schema import CompetitorAnalysisRequest
from app.models.company_model import Company

from app.core.multitenancy import (get_authorized_tenant_db, get_current_company)
from app.schemas.competitor_schema import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorReturnResponse
)
from app.service.competitor_service import (
    create_competitor,
    get_all_competitors,
    get_competitor_by_id,
    update_competitor,
    delete_competitor,
     add_selected_competitors,
     start_competitor_analysis,
     get_competitor_analysis,
)

router = APIRouter(
    prefix="/competitors",
    tags=["Competitors"],
)
@router.post(
    "/add",
    response_model=list[CompetitorResponse],
)
def add_multiple_competitors(
    competitors: list[CompetitorCreate],
    db: Session = Depends(get_authorized_tenant_db),
):
    return add_selected_competitors(
        db=db,
        competitors=competitors,
    )

@router.post(
    "/",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
)

def add_competitor(
    competitor: CompetitorCreate,
    db: Session = Depends(get_authorized_tenant_db),
):
    return create_competitor(
        db=db,
        competitor=competitor,
    )


@router.get(
    "/",
    response_model=CompetitorReturnResponse,
)
def list_competitors(
    page: int = 1,
    limit : int = 10,
    db: Session = Depends(get_authorized_tenant_db),
):
    return get_all_competitors(db=db,page=page,limit=limit)


@router.post("/analyze")
def analyze_competitor(
    request: CompetitorAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_authorized_tenant_db),
    current_company: Company = Depends(get_current_company),
):
    return start_competitor_analysis(
        db=db,
        request=request,
        background_tasks=background_tasks,
        current_company=current_company,
    )

@router.get(
    "/{competitor_id}/analysis",
)
def get_analysis(
    competitor_id: UUID,
    db: Session = Depends(get_authorized_tenant_db),
):
    return get_competitor_analysis(
        db=db,
        competitor_id=competitor_id,
    )

@router.get(
    "/{competitor_id}",
    response_model=CompetitorResponse,
)
def get_competitor(
    competitor_id: UUID,
    db: Session = Depends(get_authorized_tenant_db),
):
    return get_competitor_by_id(
        db,
        competitor_id,
    )


@router.put(
    "/{competitor_id}",
    response_model=CompetitorResponse,
)
def edit_competitor(
    competitor_id: UUID,
    competitor: CompetitorUpdate,
    db: Session = Depends(get_authorized_tenant_db),
):
    return update_competitor(
        db,
        competitor_id,
        competitor,
    )


@router.delete(
    "/{competitor_id}",
)
def remove_competitor(
    competitor_id: UUID,
    db: Session = Depends(get_authorized_tenant_db),
):
    return delete_competitor(
        db,
        competitor_id,
    )

