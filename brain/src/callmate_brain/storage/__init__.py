"""Async SQLAlchemy engine/session for the `brain` schema. Migrations live in
`brain/migrations/` (Alembic) — `create_schema_and_tables` is a dev convenience only, not a
substitute for a migration when the schema needs to change after first deploy.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateSchema

from ..config import settings
from .models import Base

engine = create_async_engine(settings.database_url)
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def create_schema_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.execute(CreateSchema("brain", if_not_exists=True))
        await conn.execute(_pgvector_extension())
        await conn.run_sync(Base.metadata.create_all)


def _pgvector_extension():
    from sqlalchemy import text

    return text("CREATE EXTENSION IF NOT EXISTS vector")


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session
