from logging.config import fileConfig
from dotenv import load_dotenv
from app.core.database import Base
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

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

x_args = context.get_x_argument(as_dictionary=True)
if not x_args:
    x_opt = config.get_main_option("x")
    if x_opt:
        x_args = {}
        for arg in x_opt.split():
            k, _, v = arg.partition("=")
            x_args[k] = v

tenant_schema = x_args.get("tenant") if isinstance(x_args, dict) else None
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    print(f"DEBUG: tenant_schema is {tenant_schema}")
    with connectable.connect() as connection:
        if tenant_schema:
            # 1. Physically create the folder in Postgres if it doesn't exist
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{tenant_schema}"'))
            # 2. Tell Postgres to look ONLY inside this folder for this session
            connection.execute(text(f'SET search_path TO "{tenant_schema}"'))
            connection.commit()
            
            # 3. Prevent Alembic from looking back at the default 'public' tables
            connection.dialect.default_schema_name = tenant_schema
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=tenant_schema
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
