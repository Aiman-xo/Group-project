from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.company_model import Company
from app.schemas.authentication_schema import CompanyRegister

from app.core.security import hash_password
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

    return {
        "message": "Company registered successfully",
        "schema_name": safe_schema
    }