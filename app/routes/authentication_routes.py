from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.schemas.authentication_schema import CompanyRegister,LoginRequest
from app.service.authentication_service import register_company,login_company

router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register")
def register(
    company: CompanyRegister,
    db: Session = Depends(get_db)
):
    return register_company(
        company_data=company,
        db=db
    )

@router.post("/login")
def login(login_data:LoginRequest,db:Session=Depends(get_db)):
    return login_company(login_data,db)