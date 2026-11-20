"""Per-call orchestrator: owns the state machine and wires STT -> brain -> TTS for one call.
Knows nothing about Twilio — `media/stream_ws.py` feeds it caller audio and consumes the audio
it produces via `audio_out`, so this class is testable with just the STT/TTS/brain protocols.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import structlog
from callmate_contracts.enums import Action, CallMode, Language, SessionEndReason
from callmate_contracts.messages import (
    AgentInterrupted,
    Escalate,
    SessionEnd,
    SessionResult,
    SessionStart,
    Utterance,
)

from ..brain_client.client import BrainClient
from ..metrics.latency import LatencyRecorder, TurnSpan
from ..storage.base import CallRepository
from ..stt.base import STTProvider
from ..tts.base import TTSProvider
from .fillers import pick_filler
from .sentence_splitter import SentenceSplitter
from .state import CallState, assert_valid_transition

logger = structlog.get_logger(__name__)

AudioSink = Callable[[bytes], Awaitable[None]]
EscalateHook = Callable[[Escalate], Awaitable[None]]


class CallSession:
    def __init__(
        self,
        *,
        call_id: str,
        user_id: str,
        caller_number: str,
        mode: CallMode,
        stt: STTProvider,
        tts: TTSProvider,
        brain: BrainClient,
        audio_out: AudioSink,
        language_hint: Language = Language.AUTO,
        caller_name: str | None = None,
        forwarded_reason: str | None = None,
        on_escalate: EscalateHook | None = None,
        call_repository: CallRepository | None = None,
    ) -> None:
        self._call_id = call_id
        self._user_id = user_id
        self._caller_number = caller_number
        self._mode = mode
        self._language_hint = language_hint
        self._caller_name = caller_name
        self._forwarded_reason = forwarded_reason

        self._stt = stt
        self._tts = tts
        self._brain = brain
        self._audio_out = audio_out
        self._on_escalate = on_escalate
        self._call_repository = call_repository

        self._state = CallState.RINGING
        self._out_seq = 0
        self._started_at = 0.0
        self._latency = LatencyRecorder()
        self._active_splitter: SentenceSplitter | None = None
        self._active_span: TurnSpan | None = None
        self._active_turn_id: str | None = None
        self._active_caller_text: str = ""
        self._active_turn_started_at: datetime | None = None
        self._tasks: list[asyncio.Task[None]] = []

        self._log = logger.bind(call_id=call_id)

    @property
    def state(self) -> CallState:
        return self._state

    def _transition(self, to_state: CallState) -> None:
        assert_valid_transition(self._state, to_state)
        self._log.info("state_transition", **{"from": self._state.value, "to": to_state.value})
        self._state = to_state

    def _next_seq(self) -> int:
        self._out_seq += 1
        return self._out_seq

    async def start(self) -> None:
        self._started_at = time.monotonic()
        self._transition(CallState.GREETING)
        if self._call_repository is not None:
            try:
                await self._call_repository.start_call(
                    call_id=self._call_id,
                    user_id=self._user_id,
                    caller_number=self._caller_number,
                    started_at=datetime.now(UTC),
                )
            except Exception:
                self._log.warning("call_repository_start_call_failed", exc_info=True)
        # Open the STT connection *before* speaking, not after — Twilio starts streaming
        # inbound audio as soon as the call connects, and send_audio() silently no-ops while
        # self._ws is None. Starting STT only after the greeting finished speaking meant
        # anything the caller said during or right at the end of the greeting was dropped.
        await self._stt.start(language_hint=self._language_hint.value)
        self._tasks.append(asyncio.create_task(self._consume_stt_results()))
        # Mandatory, not configurable off (docs/HANDOFF.md §4). TODO: personalize with the
        # user's first name/pronouns once there's a lightweight brain REST lookup for them —
        # pipeline doesn't currently have access to that profile data.
        await self._speak(
            "Hi, this is your assistant. They can't take the call right now. "
            "This call is recorded so I can pass on your message. How can I help?"
        )
        await self._brain.start_session(
            SessionStart(
                call_id=self._call_id,
                seq=self._next_seq(),
                user_id=self._user_id,
                caller_number=self._caller_number,
                caller_name=self._caller_name,
                mode=self._mode,
                language_hint=self._language_hint,
                forwarded_reason=self._forwarded_reason,
            )
        )
        self._transition(CallState.LISTENING)
        self._tasks.append(asyncio.create_task(self._consume_brain_replies()))

    async def handle_caller_audio(self, chunk: bytes) -> None:
        await self._stt.send_audio(chunk)

    async def handle_barge_in(self, spoken_text: str) -> None:
        if self._state != CallState.SPEAKING:
            return
        await self._tts.cancel()
        await self._brain.send_agent_interrupted(
            AgentInterrupted(
                call_id=self._call_id, seq=self._next_seq(), spoken_text=spoken_text
            )
        )
        self._transition(CallState.LISTENING)

    async def _consume_stt_results(self) -> None:
        async for result in self._stt.results():
            if not result.is_final or self._state != CallState.LISTENING:
                continue
            self._transition(CallState.THINKING)
            span = self._latency.new_span(turn_id=f"turn-{self._next_seq()}", call_id=self._call_id)
            span.mark("eot_detected")
            span.mark("final_transcript")
            self._active_span = span
            now = datetime.now(UTC)
            self._active_turn_id = span.turn_id
            self._active_caller_text = result.text
            self._active_turn_started_at = now
            await self._brain.send_utterance(
                Utterance(
                    call_id=self._call_id,
                    seq=self._next_seq(),
                    text=result.text,
                    language=self._language_hint,
                    confidence=result.confidence,
                    started_at=now,
                    ended_at=now,
                )
            )

    async def _consume_brain_replies(self) -> None:
        async for message in self._brain.replies():
            match message.type:
                case "reply.delta":
                    await self._handle_reply_delta(message.text)
                case "reply.done":
                    await self._handle_reply_done(message.action, message.full_text)
                case "priority.update":
                    self._log.info(
                        "priority_update", score=message.score, level=message.level.value
                    )
                case "escalate":
                    self._transition(CallState.ESCALATING)
                    if self._on_escalate is not None:
                        await self._on_escalate(message)
                case "error":
                    self._log.warning("brain_error", code=message.code, retryable=message.retryable)
                    if not message.retryable:
                        await self._speak(pick_filler())

    async def _handle_reply_delta(self, text: str) -> None:
        if self._active_span is not None and "brain_first_token" not in self._active_span.marks:
            self._active_span.mark("brain_first_token")
        if self._active_splitter is None:
            self._active_splitter = SentenceSplitter()
        for chunk in self._active_splitter.feed(text):
            await self._speak(chunk)

    async def _handle_reply_done(self, action: Action, full_text: str) -> None:
        if self._active_splitter is not None:
            remainder = self._active_splitter.flush()
            if remainder:
                await self._speak(remainder)
        self._active_splitter = None
        self._active_span = None

        if (
            self._call_repository is not None
            and self._active_turn_id is not None
            and self._active_turn_started_at is not None
        ):
            try:
                await self._call_repository.add_turn(
                    turn_id=self._active_turn_id,
                    call_id=self._call_id,
                    caller_text=self._active_caller_text,
                    agent_text=full_text,
                    started_at=self._active_turn_started_at,
                )
            except Exception:
                self._log.warning("call_repository_add_turn_failed", exc_info=True)
        self._active_turn_id = None
        self._active_turn_started_at = None

        match action:
            case Action.CONTINUE | Action.TAKE_MESSAGE:
                self._transition(CallState.LISTENING)
            case Action.ESCALATE:
                self._transition(CallState.ESCALATING)
            case Action.END_CALL:
                self._transition(CallState.CLOSING)

    async def _speak(self, text: str) -> None:
        if self._state == CallState.THINKING:
            self._transition(CallState.SPEAKING)
        if self._active_span is not None and "tts_first_byte" not in self._active_span.marks:
            self._active_span.mark("tts_first_byte")
        first_frame = True
        async for chunk in self._tts.synthesize(text):
            if first_frame and self._active_span is not None:
                self._active_span.mark("first_audio_sent")
                first_frame = False
            await self._audio_out(chunk.audio)

    async def close(self, reason: SessionEndReason) -> SessionResult:
        for task in self._tasks:
            task.cancel()
        # Wait for the cancellation to actually land before end_session() below starts its
        # own read loop on the same brain WebSocket — _consume_brain_replies() was reading
        # that connection too, and `websockets` doesn't support two concurrent readers on
        # one connection. Cancel-without-awaiting left a race where both loops could touch
        # the socket at once, corrupting it (observed as "no close frame received or sent").
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self._stt.close()
        if self._state != CallState.CLOSING:
            self._transition(CallState.CLOSING)
        duration_s = time.monotonic() - self._started_at
        result = await self._brain.end_session(
            SessionEnd(
                call_id=self._call_id,
                seq=self._next_seq(),
                reason=reason,
                duration_s=duration_s,
            )
        )
        await self._brain.close()
        if self._call_repository is not None:
            try:
                await self._call_repository.end_call(
                    call_id=self._call_id,
                    ended_at=datetime.now(UTC),
                    duration_s=duration_s,
                    end_reason=reason.value,
                )
            except Exception:
                self._log.warning("call_repository_end_call_failed", exc_info=True)
        return result
