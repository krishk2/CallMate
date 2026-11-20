"""SQLAlchemy-backed `CallRepository` (base.py). Backs the live call path
(`session/call_session.py`) and `api/turns.py`'s GET endpoint — nothing wrote to
`pipeline.calls`/`pipeline.turns` before this; the tables existed only as unused models.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .models import CallRow, TurnRow


class SqlCallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def start_call(
        self, *, call_id: str, user_id: str, caller_number: str, started_at: datetime
    ) -> None:
        self._session.add(
            CallRow(
                call_id=call_id,
                user_id=user_id,
                caller_number=caller_number,
                started_at=started_at,
            )
        )
        await self._session.commit()

    async def add_turn(
        self,
        *,
        turn_id: str,
        call_id: str,
        caller_text: str,
        agent_text: str | None,
        started_at: datetime,
    ) -> None:
        self._session.add(
            TurnRow(
                turn_id=turn_id,
                call_id=call_id,
                caller_text=caller_text,
                agent_text=agent_text,
                started_at=started_at,
            )
        )
        await self._session.commit()

    async def end_call(
        self, *, call_id: str, ended_at: datetime, duration_s: float, end_reason: str
    ) -> None:
        row = await self._session.get(CallRow, call_id)
        if row is not None:
            row.ended_at = ended_at
            row.duration_s = duration_s
            row.end_reason = end_reason
            await self._session.commit()
