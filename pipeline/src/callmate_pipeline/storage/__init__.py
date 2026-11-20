"""Async SQLAlchemy engine/session for the `pipeline` schema.

No Alembic here (by design, docs/HANDOFF.md §3 only lists `migrations/` under `brain/`):
for now, `Base.metadata.create_all` is enough for local dev. Revisit with a pipeline-owned
Alembic setup if the schema outgrows ad-hoc `create_all` before the demo.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateSchema

from ..config import settings
from .models import Base

# statement_cache_size=0 disables asyncpg's prepared-statement cache, required when
# DATABASE_URL points at a PgBouncer-pooled endpoint in transaction mode (e.g. Neon's
# "-pooler" hostname) — otherwise cached statements get reused across unrelated pooled
# connections and asyncpg raises "prepared statement ... does not exist" errors.
engine = create_async_engine(settings.database_url, connect_args={"statement_cache_size": 0})
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def create_schema_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.execute(CreateSchema("pipeline", if_not_exists=True))
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session
