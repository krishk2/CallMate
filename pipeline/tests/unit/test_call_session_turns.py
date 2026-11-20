"""CallSession persists each (caller_text, agent_text) pair through its CallRepository —
storage/base.py's protocol, satisfied here by a fake so no DB is needed.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

import pytest
from callmate_contracts.enums import CallMode, Language, SessionEndReason
from callmate_pipeline.brain_client.echo_brain import EchoBrainClient
from callmate_pipeline.session.call_session import CallSession
from callmate_pipeline.stt.mock import MockSTTProvider
from callmate_pipeline.tts.mock import MockTTSProvider


@dataclass
class FakeCallRepository:
    started: list[dict] = field(default_factory=list)
    turns: list[dict] = field(default_factory=list)
    ended: list[dict] = field(default_factory=list)

    async def start_call(
        self, *, call_id: str, user_id: str, caller_number: str, started_at: datetime
    ) -> None:
        self.started.append(
            {
                "call_id": call_id,
                "user_id": user_id,
                "caller_number": caller_number,
                "started_at": started_at,
            }
        )

    async def add_turn(
        self,
        *,
        turn_id: str,
        call_id: str,
        caller_text: str,
        agent_text: str | None,
        started_at: datetime,
    ) -> None:
        self.turns.append(
            {
                "turn_id": turn_id,
                "call_id": call_id,
                "caller_text": caller_text,
                "agent_text": agent_text,
                "started_at": started_at,
            }
        )

    async def end_call(
        self, *, call_id: str, ended_at: datetime, duration_s: float, end_reason: str
    ) -> None:
        self.ended.append(
            {
                "call_id": call_id,
                "ended_at": ended_at,
                "duration_s": duration_s,
                "end_reason": end_reason,
            }
        )


async def _wait_until(predicate, *, timeout: float = 2.0) -> None:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() > deadline:
            raise AssertionError("timed out waiting for condition")
        await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_turn_is_persisted_with_caller_and_agent_text():
    repo = FakeCallRepository()
    session = CallSession(
        call_id="call-1",
        user_id="demo",
        caller_number="+15551234567",
        mode=CallMode.SCREEN_UNKNOWN,
        stt=MockSTTProvider(["hello there"]),
        tts=MockTTSProvider(),
        brain=EchoBrainClient(),
        audio_out=lambda _chunk: asyncio.sleep(0),
        language_hint=Language.AUTO,
        call_repository=repo,
    )
    await session.start()
    assert len(repo.started) == 1
    assert repo.started[0]["call_id"] == "call-1"

    for _ in range(50):  # MockSTTProvider emits its scripted line every 50 frames
        await session.handle_caller_audio(b"\x00")

    await _wait_until(lambda: len(repo.turns) == 1)
    turn = repo.turns[0]
    assert turn["caller_text"] == "hello there"
    assert turn["agent_text"] == "You said: hello there"

    await session.close(SessionEndReason.CALLER_HANGUP)
    assert len(repo.ended) == 1
    assert repo.ended[0]["call_id"] == "call-1"
