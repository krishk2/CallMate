"""Stand-in brain for independent pipeline development (BRAIN_MODE=echo, docs/HANDOFF.md §9.2):
replies "You said: ..." to every utterance and returns a fixed session.result. No network.
"""

from __future__ import annotations

import asyncio
import itertools
from collections.abc import AsyncIterator

from callmate_contracts.enums import Action, Intent, Priority
from callmate_contracts.messages import (
    AgentInterrupted,
    BrainToPipelineMessage,
    ReplyDelta,
    ReplyDone,
    SessionEnd,
    SessionResult,
    SessionStart,
    Utterance,
)

from .client import BrainClient


class EchoBrainClient(BrainClient):
    def __init__(self) -> None:
        self._call_id = ""
        self._queue: asyncio.Queue[BrainToPipelineMessage] = asyncio.Queue()
        self._turn_ids = itertools.count(1)
        self._seq = itertools.count(1)

    async def start_session(self, start: SessionStart) -> None:
        self._call_id = start.call_id

    async def send_utterance(self, utterance: Utterance) -> None:
        turn_id = f"echo-{next(self._turn_ids)}"
        text = f"You said: {utterance.text}"
        await self._queue.put(
            ReplyDelta(call_id=self._call_id, seq=next(self._seq), turn_id=turn_id, text=text)
        )
        await self._queue.put(
            ReplyDone(
                call_id=self._call_id,
                seq=next(self._seq),
                turn_id=turn_id,
                full_text=text,
                action=Action.CONTINUE,
                language=utterance.language,
            )
        )

    async def send_agent_interrupted(self, interrupted: AgentInterrupted) -> None:
        return None

    async def replies(self) -> AsyncIterator[BrainToPipelineMessage]:
        while True:
            yield await self._queue.get()

    async def end_session(self, end: SessionEnd) -> SessionResult:
        return SessionResult(
            call_id=self._call_id,
            seq=next(self._seq),
            priority_level=Priority.NORMAL,
            score=30,
            intent=Intent.OTHER,
            summary="Echo brain session (no real priority/intent logic).",
            callback_needed=False,
            reason="echo_mode",
        )

    async def close(self) -> None:
        return None
