# upgrade_tenants.py
import sys
import os

# This file help us developers to run the migration when we modify any tenant table field or add any new model then after comaparing with any existing_schema
# Like tenatn_testing_3 after creating the migration file we run this like by upgrade_tenants.py then this runs the changes to all the tenants.

# =====> first run this command =====>
# 1. Generate the migration file (dummy_tenant is just a placeholder for autogenerate analysis)

# ./groupenv/bin/alembic-calembic_tenant.ini-xtenant=tenant_testing_3revision--autogenerate-m"add revenue to competitors"
# ====> then run this command ======>
# python upgrade_tenants.py ==> this is the command

# Ensure the app root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import sessionLocal
from app.models.company_model import Company
from app.core.multitenancy import create_tenant_schema_tables

def upgrade_all_existing_tenants():
    db = sessionLocal()
    try:
        # 1. Fetch all verified companies
        companies = db.query(Company).filter(Company.is_verified == True).all()
        print(f"Found {len(companies)} registered companies to upgrade.")

        for company in companies:
            if company.schema_name:
                print(f"Upgrading schema '{company.schema_name}' for {company.company_name}...")
                try:
                    # Drop the old public-timeline alembic_version table from this schema
                    from sqlalchemy import text
                    db.execute(text(f'DROP TABLE IF EXISTS "{company.schema_name}".alembic_version CASCADE'))
                    db.commit()
                    
                    # 2. Run the migration head for this specific schema
                    create_tenant_schema_tables(company.schema_name)
                    print(f"Successfully upgraded '{company.schema_name}'")
                except Exception as err:
                    print(f"❌ Failed to upgrade '{company.schema_name}': {err}")
    finally:
        db.close()

if __name__ == "__main__":
    upgrade_all_existing_tenants()
