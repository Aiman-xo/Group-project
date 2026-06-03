from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.company_model import Company
from app.schemas.authentication_schema import CompanyRegister,LoginRequest

from app.core.security import hash_password,create_access_token,create_refresh_token,verify_password
from app.core.multitenancy import create_tenant_schema_tables



def register_company(
    company_data: CompanyRegister,
    db: Session
):

    # Check email already exists
    existing_company = db.query(Company).filter(
        Company.email == company_data.email
    ).first()

    if existing_company:
        return {
            "message": "Email already registered"
        }

    # Generate tenant schema name
    safe_schema = (
        f"tenant_{company_data.company_name.lower().replace(' ', '_')}"
    )

    # Create schema physically in postgres
    db.execute(
        text(
            f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'
        )
    )

    db.commit()

    # Run tenant migration
    create_tenant_schema_tables(
        safe_schema
    )

    # Hash password
    hashed_password = hash_password(
        company_data.password
    )

    # Save company
    new_company = Company(
        email=company_data.email,
        company_name=company_data.company_name,
        website_link=company_data.website_link,
        industry=company_data.industry,
        password=hashed_password,
        schema_name=safe_schema
    )

    db.add(new_company)

    db.commit()

    db.refresh(new_company)

    access_token = create_access_token(
        data={
            "sub": company_data.email
        }
    )

    refresh_token = create_refresh_token(
    data={
        "sub": company_data.email
    }
)

    return {
        "message": "Company registered successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "schema_name": safe_schema
    }



def login_company(login_data:LoginRequest,db:Session):
    company=db.query(Company).filter(Company.email==login_data.email).first()
    if not company:
        return {"message":"Invalid Email and Password"}
    if not verify_password(login_data.password,company.password):
        return{
            "message":"Invalid Email and Password"
        }
    access_token=create_access_token(
        data={
            "sub":company.email
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": company.email
        }
    )
    return{
        "message":"Login Successfully",
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearer",
        "schema_name":company.schema_name
    }
def forget_password(l):
    pass

