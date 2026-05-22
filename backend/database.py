"""Async SQLAlchemy database engine, session factory, and migration bootstrap."""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import settings

logger = logging.getLogger(__name__)

# Connection pool: pre-ping stale connections; pool_size for concurrent requests
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.node_env == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _resolve_migrations_dir() -> Path:
    """Resolve migration SQL directory (Docker mount or repo db/migrations)."""
    if settings.migrations_dir:
        return Path(settings.migrations_dir)
    docker_path = Path("/app/migrations")
    if docker_path.is_dir():
        return docker_path
    return Path(__file__).resolve().parent.parent / "db" / "migrations"


def _load_migration_files() -> list[Path]:
    """Return sorted SQL migration files from the migrations directory."""
    migrations_dir = _resolve_migrations_dir()
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        raise FileNotFoundError(f"No migration files found in: {migrations_dir}")
    return files


def _split_sql_statements(sql: str) -> list[str]:
    """Split a PostgreSQL script into statements (respects DO $tag$ ... END $tag$ blocks)."""
    import re

    statements: list[str] = []
    buffer: list[str] = []
    in_dollar_block = False
    dollar_open = re.compile(r"DO\s+\$[a-zA-Z_]*\$", re.IGNORECASE)
    dollar_close = re.compile(r"END\s+\$[a-zA-Z_]*\$;\s*$", re.IGNORECASE)

    for line in sql.splitlines():
        stripped = line.strip()
        if not in_dollar_block and (not stripped or stripped.startswith("--")):
            continue

        buffer.append(line)

        if not in_dollar_block and dollar_open.search(line):
            in_dollar_block = True
            continue

        if in_dollar_block:
            if dollar_close.search(stripped):
                in_dollar_block = False
                statement = "\n".join(buffer).strip()
                if statement:
                    statements.append(statement)
                buffer = []
            continue

        if stripped.endswith(";"):
            statement = "\n".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []

    remainder = "\n".join(buffer).strip()
    if remainder:
        statements.append(remainder)
    return statements


async def init_db() -> None:
    """Run idempotent migration SQL on startup."""
    import models  # noqa: F401 — ensure ORM models are registered

    migration_files = _load_migration_files()
    total_statements = 0

    async with engine.begin() as conn:
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            statements = _split_sql_statements(sql)
            for statement in statements:
                await conn.execute(text(statement))
            total_statements += len(statements)
            logger.info("Applied migration: %s (%d statements)", migration_file.name, len(statements))

    logger.info("Database initialised (%d statements across %d files).", total_statements, len(migration_files))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Dispose the async engine and connection pool."""
    await engine.dispose()


def create_engine_for_tests(database_url: str) -> AsyncEngine:
    """Create a single-connection engine for isolated tests."""
    return create_async_engine(database_url, poolclass=NullPool)
