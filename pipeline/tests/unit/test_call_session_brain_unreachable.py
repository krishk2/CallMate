"""Regression test for a real incident: brain was asleep (free-tier cold start) when a call
came in, and its WebSocket handshake rejected with HTTP 502. That exception was unhandled in
CallSession.start(), crashing the ASGI handler right after the greeting played — the caller
heard "hi" then got dropped with no explanation. start() must now speak an apology and end
the call gracefully instead of raising.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from callmate_contracts.enums import CallMode, Language
from callmate_contracts.messages import (
    AgentInterrupted,
    BrainToPipelineMessage,
    SessionEnd,
    SessionResult,
    SessionStart,
    Utterance,
)
from callmate_pipeline.brain_client.client import BrainClient
from callmate_pipeline.session.call_session import CallSession
from callmate_pipeline.session.state import CallState
from callmate_pipeline.stt.mock import MockSTTProvider
from callmate_pipeline.tts.mock import MockTTSProvider


class AlwaysDownBrainClient(BrainClient):
    async def start_session(self, start: SessionStart) -> None:
        raise ConnectionError("server rejected WebSocket connection: HTTP 502")

    async def send_utterance(self, utterance: Utterance) -> None:
        return None

    async def send_agent_interrupted(self, interrupted: AgentInterrupted) -> None:
        return None

    async def replies(self) -> AsyncIterator[BrainToPipelineMessage]:
        return
        yield  # pragma: no cover - unreachable, just satisfies the generator protocol

    async def end_session(self, end: SessionEnd) -> SessionResult:
        raise ConnectionError("still down")

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_start_degrades_gracefully_when_brain_is_unreachable():
    async def audio_out(_chunk: bytes) -> None:
        return None

    session = CallSession(
        call_id="call-brain-down",
        user_id="demo",
        caller_number="+15551234567",
        mode=CallMode.SCREEN_UNKNOWN,
        stt=MockSTTProvider([]),
        tts=MockTTSProvider(),
        brain=AlwaysDownBrainClient(),
        audio_out=audio_out,
        language_hint=Language.AUTO,
    )

    await asyncio.wait_for(session.start(), timeout=2.0)  # must not raise

    assert session.state == CallState.CLOSING
