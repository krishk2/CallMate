"""`GET /v1/calls/{call_id}/turns` — the turn-by-turn transcript (caller text + agent reply,
per turn) that `session/call_session.py` now writes via `storage/repositories.py`. Requires
SERVICE_TOKEN like `telephony/outbound.py`, since a transcript is caller content.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..auth import require_service_token
from ..storage import get_session
from ..storage.models import CallRow, TurnRow

router = APIRouter()


class TurnItem(BaseModel):
    turn_id: str
    caller_text: str
    agent_text: str | None
    started_at: datetime


@router.get(
    "/v1/calls/{call_id}/turns",
    response_model=list[TurnItem],
    dependencies=[Depends(require_service_token)],
)
async def list_turns(call_id: str) -> list[TurnItem]:
    async with get_session() as db:
        call = await db.get(CallRow, call_id)
        if call is None:
            raise HTTPException(status_code=404, detail="call not found")
        rows = (
            (
                await db.execute(
                    select(TurnRow)
                    .where(TurnRow.call_id == call_id)
                    .order_by(TurnRow.started_at)
                )
            )
            .scalars()
            .all()
        )
        return [
            TurnItem(
                turn_id=row.turn_id,
                caller_text=row.caller_text,
                agent_text=row.agent_text,
                started_at=row.started_at,
            )
            for row in rows
        ]
