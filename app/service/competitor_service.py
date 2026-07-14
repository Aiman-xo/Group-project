from sqlalchemy.orm import Session
from fastapi import HTTPException, status,BackgroundTasks
from uuid import UUID
import uuid

from app.utils.slug import generate_slug
from app.core.logger import logger
from app.models.company_model import Company
from app.models.competetor_analyser import CompetetorAnalyser,CompetitorComparison

from app.schemas.analysis_schema import CompetitorAnalysisRequest
from app.service.background_tasks import run_background_crawler_pipeline

from app.models.competitor_model import Competitor
from app.schemas.competitor_schema import (
    CompetitorCreate,
    CompetitorUpdate,
)



def create_competitor(
    db: Session,
    competitor: CompetitorCreate,
):
    existing = (
        db.query(Competitor)
        .filter(
            Competitor.website_url == competitor.website_url
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Competitor already exists.",
        )
    
    slug = generate_slug(competitor.company_name)

    existing_slug = (
        db.query(Competitor)
        .filter(Competitor.slug == slug)
        .first()
    )

    if existing_slug:
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"
    

    new_competitor = Competitor(
        company_name=competitor.company_name,
        website_url=competitor.website_url,
        industry=competitor.industry,
        location=competitor.location,
        description=competitor.description,
        slug=slug,

    )

    try:
        db.add(new_competitor)
        db.commit()
        db.refresh(new_competitor)
        return new_competitor

    except Exception:
        db.rollback()
        raise

def add_selected_competitors(
    db: Session,
    competitors: list[CompetitorCreate],
):
    saved_competitors = []

    for competitor in competitors:
        existing = (
            db.query(Competitor)
            .filter(
                Competitor.website_url == competitor.website_url
            )
            .first()
        )

        # Skip duplicates
        if existing:
            continue

        slug = generate_slug(competitor.company_name)

        existing_slug = (
            db.query(Competitor)
            .filter(Competitor.slug == slug)
            .first()
        )
        if existing_slug:
            slug = f"{slug}-{str(uuid.uuid4())[:8]}"


        new_competitor = Competitor(
            company_name=competitor.company_name,
            website_url=competitor.website_url,
            industry=competitor.industry,
            location=competitor.location,
            description=competitor.description,
            slug=slug,

        )

        db.add(new_competitor)
        saved_competitors.append(new_competitor)

    try:
        db.commit()

        for competitor in saved_competitors:
            db.refresh(competitor)

        return get_all_competitors(db)

    except Exception:
        db.rollback()
        raise
    
def get_all_competitors(
    db:Session,
    page,
    limit
):
    try:
        page = int(page)
        limit = int(limit)
        
        offset = (page - 1) * limit
        competitors = db.query(Competitor).order_by(Competitor.created_at.desc()).offset(offset).limit(limit).all()
        total = db.query(Competitor).count()

        return {
            'competitors':competitors,
            "total":total,
            "page":page,
            "limit":limit
        }
    except Exception as e:
        logger.error(f'Error fetching competitors: {e}')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Couldnt Fetch Competitors')


def get_competitor_by_id(
    db: Session,
    competitor_id: UUID,
):
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.id == competitor_id
        )
        .first()
    )

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found.",
        )

    return competitor


def update_competitor(
    db: Session,
    competitor_id: UUID,
    competitor: CompetitorUpdate,
):
    db_competitor = get_competitor_by_id(
        db,
        competitor_id,
    )

    # Prevent duplicate website URLs
    if (
        competitor.website_url
        and competitor.website_url != db_competitor.website_url
    ):
        existing = (
            db.query(Competitor)
            .filter(
                Competitor.website_url == competitor.website_url
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Website URL already exists.",
            )

    update_data = competitor.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(
            db_competitor,
            key,
            value,
        )

    try:
        db.commit()
        db.refresh(db_competitor)
        return db_competitor

    except Exception:
        db.rollback()
        raise


def delete_competitor(
    db: Session,
    competitor_id: UUID,
):
    competitor = get_competitor_by_id(
        db,
        competitor_id,
    )

    try:
        db.delete(competitor)
        db.commit()

        return {
            "message": "Competitor deleted successfully."
        }

    except Exception:
        db.rollback()
        raise

def start_competitor_analysis(
    db: Session,
    request: CompetitorAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_company: Company,
):
    competitor = (
        db.query(Competitor)
        .filter(Competitor.slug == request.slug)
        .first()
    )

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found."
        )

    background_tasks.add_task(
        run_background_crawler_pipeline,
        company_id=f"company_{current_company.slug}",
        company_name=competitor.company_name,
        website_url=competitor.website_url,
        is_competitor=True,
    )

    return {
        "message": "Competitor analysis started.",
        "company_name":competitor.company_name,
        "slug": competitor.slug,
    }

def get_competitor_analysis(
    db: Session,
    competitor_id: UUID,
):
    competitor = (
        db.query(Competitor)
        .filter(Competitor.id == competitor_id)
        .first()
    )

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found."
        )

    analysis = (
        db.query(CompetetorAnalyser)
        .filter(
            CompetetorAnalyser.competitor_id == competitor_id,
            CompetetorAnalyser.is_latest == True,
        )
        .first()
    )

    comparison = None

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis is not found."
        )

    if analysis:
        comparison = (
            db.query(CompetitorComparison)
            .filter(
                CompetitorComparison.competitor_id == analysis.id,
                CompetitorComparison.is_latest == True,
            )
            .first()
        )

    return {
        "competitor": competitor,
        "analysis": analysis,
        "comparison": comparison,
    }