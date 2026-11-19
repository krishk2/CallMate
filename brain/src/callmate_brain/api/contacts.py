"""GET call-context (docs/HANDOFF.md §5.3 — pipeline's routing.py calls this and needs an
answer in < 150ms) and contact import."""

from __future__ import annotations

from callmate_contracts.rest import CallContextResponse
from fastapi import APIRouter

from ..storage import get_session
from ..storage.repositories import SqlContactRepository

router = APIRouter(prefix="/v1/users")


@router.get("/{user_id}/call-context", response_model=CallContextResponse)
async def call_context(user_id: str, caller: str) -> CallContextResponse:
    async with get_session() as db:
        return await SqlContactRepository(db).call_context(user_id, caller)


@router.post("/{user_id}/contacts/import")
async def import_contacts(user_id: str, contacts: list[dict[str, str]]) -> dict[str, int]:
    async with get_session() as db:
        count = await SqlContactRepository(db).import_contacts(user_id, contacts)
        return {"imported": count}
