"""Alembic environment configuration."""
import os
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(f"DATABASE_URL is not set. Check your .env file at {env_path}")

# Use synchronous psycopg2 driver for Alembic
# Strip asyncpg-specific query params and convert ssl=require -> sslmode=require
import re

def _make_sync_url(url: str) -> str:
    url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    url = url.replace("postgresql+aiopg", "postgresql+psycopg2")
    # Replace ?ssl=require with ?sslmode=require (psycopg2 uses sslmode)
    url = re.sub(r'[?&]ssl=require', '', url)
    if 'sslmode' not in url:
        sep = '&' if '?' in url else '?'
        url = url + sep + 'sslmode=require'
    return url

SYNC_DATABASE_URL = _make_sync_url(DATABASE_URL)

# Alembic Config object
config = context.config
config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import ALL models so Alembic can detect schema changes
from app.database.base import Base  # noqa: F401
import app.models  # noqa: F401 — registers all models on Base.metadata

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection required)."""
    url = config.get_main_option("sqlalchemy.url")
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
    """Run migrations in 'online' mode (live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
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
