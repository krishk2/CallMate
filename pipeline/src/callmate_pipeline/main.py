from __future__ import annotations

from fastapi import FastAPI

from .media.stream_ws import router as media_router
from .telephony.twilio_webhooks import router as twilio_router


def create_app() -> FastAPI:
    app = FastAPI(title="CallMate Pipeline")
    app.include_router(twilio_router)
    app.include_router(media_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
