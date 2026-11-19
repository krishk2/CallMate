from __future__ import annotations

from fastapi import FastAPI

from .api.calls import router as calls_router
from .api.contacts import router as contacts_router
from .api.memories import router as memories_router
from .api.session_ws import router as session_ws_router
from .api.users import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="CallMate Brain")
    app.include_router(users_router)
    app.include_router(contacts_router)
    app.include_router(memories_router)
    app.include_router(calls_router)
    app.include_router(session_ws_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
