from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.multitenancy import (
    get_current_company,
    get_authorized_tenant_db,
)
from app.models.company_model import ProfileDataAnalyser
from app.schemas.instagram_schema import InstagramUrlUpdate
from app.service.instagram.instagram_service import InstagramService


router = APIRouter(
    prefix="/instagram",
    tags=["Instagram"]
)

instagram_service = InstagramService()


# =========================================================
# Check Instagram URL
# =========================================================

@router.get("/connection-status")
def check_instagram_connection(
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):

    profile = (
        db.query(ProfileDataAnalyser)
        .filter(
            ProfileDataAnalyser.company_id == current_company.id,
            ProfileDataAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    if not profile.instagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company Instagram URL not found"
        )

    return {
        "connected": True,
        "instagram_url": profile.instagram
    }


# =========================================================
# Add / Edit Instagram URL
# =========================================================

@router.put("/instagram-url")
def update_instagram_profile_url(
    payload: InstagramUrlUpdate,
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    profile = (
        db.query(ProfileDataAnalyser)
        .filter(
            ProfileDataAnalyser.company_id == current_company.id,
            ProfileDataAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    profile.instagram = payload.instagram_url

    db.commit()

    return {
        "instagram_url": payload.instagram_url
    }

# =========================================================
# Connect / Analyze Instagram
# =========================================================

@router.post("/connect")
def connect_instagram(
    db: Session = Depends(get_authorized_tenant_db),
    current_company=Depends(get_current_company),
):
    profile = (
        db.query(ProfileDataAnalyser)
        .filter(
            ProfileDataAnalyser.company_id == current_company.id,
            ProfileDataAnalyser.is_latest.is_(True)
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    if not profile.instagram:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram URL not found"
        )

    # success = instagram_service.process_instagram(
    #     company_slug=str(current_company.slug),
    #     company_name=current_company.company_name,
    #     instagram_url=profile.instagram,
    #     is_competitor=False,
    # )
    success = instagram_service.process_instagram(
        db=db,
        company_id=current_company.id,
        company_slug=str(current_company.slug),
        company_name=current_company.company_name,
        instagram_url=profile.instagram,
        is_competitor=False,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to fetch Instagram data"
        )

    return {
        "success": True,
        "message": "Instagram data collected successfully"
    }