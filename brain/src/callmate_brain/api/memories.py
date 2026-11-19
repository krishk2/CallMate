"""DELETE /v1/users/{id}/memories[/...] — user control over stored memories
(docs/HANDOFF.md §5.3, §8)."""

from __future__ import annotations

from fastapi import APIRouter

from ..storage import get_session
from ..storage.repositories import SqlLongTermMemoryStore

router = APIRouter(prefix="/v1/users")


@router.delete("/{user_id}/memories/{memory_id}")
async def delete_memory(user_id: str, memory_id: str) -> dict[str, str]:
    async with get_session() as db:
        await SqlLongTermMemoryStore(db).delete(user_id, memory_id)
        return {"status": "deleted"}


@router.delete("/{user_id}/memories")
async def delete_all_memories(user_id: str) -> dict[str, str]:
    async with get_session() as db:
        await SqlLongTermMemoryStore(db).delete_all(user_id)
        return {"status": "deleted_all"}
