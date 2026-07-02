from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.multitenancy import get_authorized_tenant_db
from app.schemas.competitor_schema import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
)
from app.service.competitor_service import (
    create_competitor,
    get_all_competitors,
    get_competitor_by_id,
    update_competitor,
    delete_competitor,
)

router = APIRouter(
    prefix="/competitors",
    tags=["Competitors"],
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
    response_model=list[CompetitorResponse],
)
def list_competitors(
    db: Session = Depends(get_authorized_tenant_db),
):
    return get_all_competitors(db)


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