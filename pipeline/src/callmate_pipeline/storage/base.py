"""`CallRepository` protocol — what `session/call_session.py` needs to persist a call and its
turns, independent of SQLAlchemy. Keeps `CallSession` testable with a fake, matching the
STT/TTS/brain protocols it already depends on (`stt/base.py`, `tts/base.py`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class CallRepository(Protocol):
    async def start_call(
        self, *, call_id: str, user_id: str, caller_number: str, started_at: datetime
    ) -> None:
        """Record that a call started. Called once, from `CallSession.start()`."""

    async def add_turn(
        self,
        *,
        turn_id: str,
        call_id: str,
        caller_text: str,
        agent_text: str | None,
        started_at: datetime,
    ) -> None:
        """Record one caller-utterance/agent-reply pair. Called once per turn."""

    async def end_call(
        self, *, call_id: str, ended_at: datetime, duration_s: float, end_reason: str
    ) -> None:
        """Record call end. Called once, from `CallSession.close()`."""
