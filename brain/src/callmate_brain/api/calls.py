"""GET call history for the user (docs/HANDOFF.md §5.3)."""

from __future__ import annotations

from callmate_contracts.rest import CallDetail, CallSummaryItem
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..storage import get_session
from ..storage.models import CallRow

router = APIRouter()


@router.get("/v1/users/{user_id}/calls", response_model=list[CallSummaryItem])
async def list_calls(user_id: str) -> list[CallSummaryItem]:
    async with get_session() as db:
        rows = (
            (await db.execute(select(CallRow).where(CallRow.user_id == user_id))).scalars().all()
        )
        return [
            CallSummaryItem(
                call_id=row.call_id,
                caller_number=row.caller_number,
                started_at=row.started_at,
                duration_s=row.duration_s,
                priority_level=row.priority_level,
                intent=row.intent,
                summary=row.summary,
            )
            for row in rows
        ]


@router.get("/v1/calls/{call_id}", response_model=CallDetail)
async def get_call(call_id: str) -> CallDetail:
    async with get_session() as db:
        row = await db.get(CallRow, call_id)
        if row is None:
            raise HTTPException(status_code=404, detail="call not found")
        return CallDetail(
            call_id=row.call_id,
            caller_number=row.caller_number,
            started_at=row.started_at,
            duration_s=row.duration_s,
            priority_level=row.priority_level,
            intent=row.intent,
            summary=row.summary,
            score=row.score,
            callback_needed=row.callback_needed,
            callback_window=row.callback_window,
            recording_url=row.recording_url,
        )
