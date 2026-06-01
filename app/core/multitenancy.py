# This function needs to be run at the time of registration before hitting the db
# This runs the migration inside the new schema we created and creates all the models that are not in the public.

import os
from alembic.config import Config
from alembic import command

def create_tenant_schema_tables(schema_name:str):
    """Programmatically runs 'alembic upgrade head' inside a specific schema"""
    # Point to your local alembic.ini file
    alembic_cfg = Config("alembic.ini")
    
    # Pass the custom schema name as an alembic -x argument dynamically!
    alembic_cfg.set_main_option("x", f"tenant={schema_name}")
    
    # Run the upgrade command to stamp all existing models into this new schema
    command.upgrade(alembic_cfg, "head")


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