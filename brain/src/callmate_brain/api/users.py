"""GET/PUT /v1/users/{id}/settings (docs/HANDOFF.md §5.3)."""

from __future__ import annotations

from callmate_contracts.rest import UserSettings
from fastapi import APIRouter, HTTPException

from ..storage import get_session
from ..storage.repositories import SqlProfileRepository

router = APIRouter(prefix="/v1/users")


@router.get("/{user_id}/settings", response_model=UserSettings)
async def get_settings(user_id: str) -> UserSettings:
    async with get_session() as db:
        try:
            profile = await SqlProfileRepository(db).get(user_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="user not found") from exc
        return profile.settings


@router.put("/{user_id}/settings", response_model=UserSettings)
async def put_settings(user_id: str, settings: UserSettings) -> UserSettings:
    async with get_session() as db:
        await SqlProfileRepository(db).update_settings(user_id, settings)
        return settings
