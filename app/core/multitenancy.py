# This function needs to be run at the time of registration before hitting the db
# This runs the migration inside the new schema we created and creates all the models that are not in the public.

import re
from pathlib import Path
from alembic.config import Config
from alembic import command
from fastapi import Depends ,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text

from sqlalchemy.orm import Session
from app.core.database import TenantBase, engine, get_db
from app.core.security import verify_token
from app.models.company_model import Company

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

TENANT_SCHEMA_RE = re.compile(r"^tenant_[a-z0-9_]+$")


def validate_tenant_schema_name(schema_name: str) -> None:
    if not TENANT_SCHEMA_RE.fullmatch(schema_name):
        raise ValueError(f"Invalid tenant schema name: {schema_name}")


def create_tenant_schema_tables(schema_name:str):
    """Programmatically runs 'alembic upgrade head' inside a specific schema"""
    validate_tenant_schema_name(schema_name)

    project_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(str(project_root / "alembic_tenant.ini"))
    
    # Programmatic equivalent of: alembic -x tenant=<schema_name> upgrade head
    alembic_cfg.attributes["tenant_schema"] = schema_name
    
    command.upgrade(alembic_cfg, "head")

    tenant_tables = TenantBase.metadata.tables.keys()
    with engine.connect() as connection:
        missing_tables = [
            table_name
            for table_name in tenant_tables
            if connection.execute(
                text("SELECT to_regclass(:qualified_table)"),
                {"qualified_table": f"{schema_name}.{table_name}"},
            ).scalar()
            is None
        ]

    if missing_tables:
        raise RuntimeError(
            f"Tenant schema '{schema_name}' is missing migrated tables: "
            f"{', '.join(sorted(missing_tables))}"
        )


async def get_current_company(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = verify_token(token)

    company_id = payload["sub"]

    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=401,
            detail="Company not found"
        )

    return company


# This is the middleware or Dependency that validates the JWT to tenant name are match. like when a company authenticate and this prevent form acessing other 
# tenants data. so how this works is that it gets the current company which is authenticated by get_current_company this dependency. and then gets the current
# schema_name by the SQL query to SHOW the search_path which is set at the time of registration. and if everything correct returns the tenant db.
from fastapi import status
from app.core.database import get_tenant_db

async def get_authorized_tenant_db(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_tenant_db)
):
    current_schema_result = db.execute(text("SHOW search_path")).fetchone()
    current_schema = current_schema_result[0] if current_schema_result else ""
    print(current_schema,'============>>>>>>')
    
    if not current_schema.startswith(f'"{current_company.schema_name}"') and not current_schema.startswith(current_company.schema_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this workspace."
        )
    return db


# NOW IN THE REGISTRATION ROUTE WE NEED TO GIVE LIKE
# =====================================================================
# safe_schema = f"tenant_{company_name.lower().replace(' ', '_')}"
    
# 2. Create the blank schema in Postgres physically
# db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'))

# ======================================================================
# 3. bootstrap_tenant_schema(safe_schema)

# example code :
# uncomment from here =========================================================

# router = APIRouter(prefix="/auth", tags=["Authentication"])

# @router.post("/register", status_code=status.HTTP_201_CREATED)
# def register_company(company_name: str, email: str, password: str, db: Session = Depends(get_db)):
#     safe_schema = f"tenant_{company_name.lower().replace(' ', '_')}"
    
#     db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'))
#     db.commit()
    
    
#     bootstrap_tenant_schema(safe_schema)

#     new_company = Company(
#         company_name=company_name,
#         email=email,
#         password=password, # Remember to hash this!
#         schema_name=safe_schema
#     )
#     db.add(new_company)
#     db.commit()
    
#     return {"message": f"Company registered and isolated schema '{safe_schema}' is ready!"}
