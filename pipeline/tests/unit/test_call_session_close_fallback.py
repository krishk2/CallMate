"""CallSession.close() must never hang (or leave send_call_summary_notifications unreachable
in media/stream_ws.py's caller) just because brain is slow or unreachable — regression test
for a real incident: brain's own summariser retrying twice pushed session.end past whatever
idle-connection allowance the deployment's network path gives a WebSocket, pipeline's
end_session() hung forever waiting for a reply that never arrived, and the Telegram/WhatsApp
notification that runs right after close() never fired.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from callmate_contracts.enums import CallMode, Language, SessionEndReason
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
from callmate_pipeline.stt.mock import MockSTTProvider
from callmate_pipeline.tts.mock import MockTTSProvider


class HangingBrainClient(BrainClient):
    """Simulates brain accepting session.end but never sending session.result back."""

    async def start_session(self, start: SessionStart) -> None:
        return None

    async def send_utterance(self, utterance: Utterance) -> None:
        return None

    async def send_agent_interrupted(self, interrupted: AgentInterrupted) -> None:
        return None

    async def replies(self) -> AsyncIterator[BrainToPipelineMessage]:
        while True:
            await asyncio.sleep(3600)
            yield  # pragma: no cover - never reached

    async def end_session(self, end: SessionEnd) -> SessionResult:
        await asyncio.sleep(3600)
        raise AssertionError("should have been cancelled by the timeout")

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_close_falls_back_instead_of_hanging_when_brain_never_replies():
    session = CallSession(
        call_id="call-hang",
        user_id="demo",
        caller_number="+15551234567",
        mode=CallMode.SCREEN_UNKNOWN,
        stt=MockSTTProvider([]),
        tts=MockTTSProvider(),
        brain=HangingBrainClient(),
        audio_out=lambda _chunk: asyncio.sleep(0),
        language_hint=Language.AUTO,
        brain_end_session_timeout_s=0.05,
    )
    await session.start()

    result = await asyncio.wait_for(
        session.close(SessionEndReason.CALLER_HANGUP), timeout=2.0
    )

    assert isinstance(result, SessionResult)
    assert result.reason == "brain_end_session_timeout"
