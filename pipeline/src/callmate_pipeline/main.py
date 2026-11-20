from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.turns import router as turns_router
from .media.stream_ws import router as media_router
from .storage import create_schema_and_tables
from .telephony.outbound import router as outbound_router
from .telephony.twilio_webhooks import router as twilio_router


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # create_all, not Alembic (storage/__init__.py) — safe to call every boot, no-ops once
    # the schema/tables already exist.
    await create_schema_and_tables()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="CallMate Pipeline", lifespan=_lifespan)
    app.include_router(twilio_router)
    app.include_router(media_router)
    app.include_router(outbound_router)
    app.include_router(turns_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
