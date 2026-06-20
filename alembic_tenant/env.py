from logging.config import fileConfig
from dotenv import load_dotenv
import os
from alembic import context
from sqlalchemy import engine_from_config, pool, text

# Import your database base and tenant models
from app.core.database import TenantBase
import app.models # ensure Competitor, CompanyProfile are imported

load_dotenv()
config = context.config

database_url = os.getenv("DATABASE_URL")
if database_url:
    database_url = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = TenantBase.metadata

# Retrieve the dynamically passed schema name
x_args = context.get_x_argument(as_dictionary=True)
if not x_args:
    x_opt = config.get_main_option("x")
    if x_opt:
        x_args = {}
        for arg in x_opt.split():
            k, _, v = arg.partition("=")
            x_args[k] = v

tenant_schema = x_args.get("tenant") if isinstance(x_args, dict) else None

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if tenant_schema:
            # 1. Create the schema physically
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{tenant_schema}"'))
            # 2. Scope this session to the tenant's schema
            connection.execute(text(f'SET search_path TO "{tenant_schema}"'))
            connection.commit()
            
            # 3. Block Alembic from reading 'public' metadata
            connection.dialect.default_schema_name = tenant_schema

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=tenant_schema, # Save the alembic_version table inside the tenant schema
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

