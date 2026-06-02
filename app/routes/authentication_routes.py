from fastapi import APIRouter
from app.service.authentication_service import login_company

router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/login")
def login():
    return login_company()