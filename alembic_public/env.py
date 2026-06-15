from logging.config import fileConfig
from dotenv import load_dotenv
from app.core.database import PublicBase
import app.models

from sqlalchemy import engine_from_config
from sqlalchemy import pool,text
import os

from alembic import context

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

database_url = os.getenv("DATABASE_URL")
if database_url:
    database_url = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = PublicBase.metadata

from app.core.database import TenantBase

# Dynamically derive tenant table names from TenantBase.metadata.
# Any new TenantBase model added in future will be automatically excluded
# from public migrations without needing to update this file.
TENANT_TABLES = set(TenantBase.metadata.tables.keys())

def include_object(object, name, type_, reflected, compare_to):
    # Exclude all tables that belong to the tenant schema
    if type_ == "table" and name in TENANT_TABLES:
        return False
    return True

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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

