from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import create_engine, pool
from app.database.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """
    Read DB URL directly from environment — works on Railway, local, and any cloud.
    Priority: DATABASE_URL env var > PGHOST/PGPORT parts > fallback default
    """
    # 1. Try DATABASE_URL directly (Railway, Heroku, Render all set this)
    url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("database_url")
        or os.environ.get("SQLALCHEMY_DATABASE_URI")
    )

    if url:
        # Normalize postgres:// -> postgresql+psycopg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://") and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    # 2. Build from individual PG* vars (Railway also exposes these)
    pg_host = os.environ.get("PGHOST")
    pg_port = os.environ.get("PGPORT", "5432")
    pg_user = os.environ.get("PGUSER")
    pg_pass = os.environ.get("PGPASSWORD")
    pg_db   = os.environ.get("PGDATABASE")

    if pg_host and pg_user and pg_db:
        return f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

    # 3. Last resort — local dev default
    return "postgresql+psycopg://postgres:postgres@localhost:5432/abiz_pos"


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
