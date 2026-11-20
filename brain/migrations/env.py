from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from callmate_brain.config import settings
from callmate_brain.storage.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Restrict autogenerate/compare to the `brain` schema only. DATABASE_URL may point at a
    database shared with unrelated projects (other schemas, or tables in `public`) — without
    this, `--autogenerate` will propose dropping tables Alembic has no business touching.
    """
    table = getattr(object, "table", None)
    schema = getattr(object, "schema", None) or getattr(table, "schema", None)
    return schema == "brain"


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        version_table_schema="brain",
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="brain",
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.database_url, connect_args={"statement_cache_size": 0})
    async with engine.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
