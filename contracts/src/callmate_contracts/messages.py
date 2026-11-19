"""WebSocket message models for the pipeline <-> brain contract (docs/HANDOFF.md §5).

Every message carries an envelope (`call_id`, `seq`, `ts`, `v`) plus a `type` discriminator.
Unknown types must never crash a session (§5.4) — use `parse_pipeline_message` /
`parse_brain_message`, which raise `UnknownMessageType` instead of a validation error so
callers can log and ignore per the contract rule.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from .enums import Action, CallMode, Intent, Language, Priority, SessionEndReason
from .version import PROTOCOL_VERSION


class UnknownMessageType(Exception):
    def __init__(self, type_value: Any) -> None:
        self.type_value = type_value
        super().__init__(f"Unknown message type: {type_value!r}")


class _Envelope(BaseModel):
    call_id: str
    seq: int
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    v: str = PROTOCOL_VERSION


# ---------------------------------------------------------------------------
# Pipeline -> Brain
# ---------------------------------------------------------------------------


class SessionStart(_Envelope):
    type: Literal["session.start"] = "session.start"
    user_id: str
    caller_number: str
    caller_name: str | None = None
    mode: CallMode
    language_hint: Language = Language.AUTO
    forwarded_reason: str | None = None


class UtterancePartial(_Envelope):
    type: Literal["utterance.partial"] = "utterance.partial"
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class Utterance(_Envelope):
    type: Literal["utterance"] = "utterance"
    text: str
    language: Language
    confidence: float = Field(ge=0.0, le=1.0)
    started_at: datetime
    ended_at: datetime
    interrupted_agent: bool = False


class AgentInterrupted(_Envelope):
    type: Literal["agent.interrupted"] = "agent.interrupted"
    spoken_text: str


class Dtmf(_Envelope):
    type: Literal["dtmf"] = "dtmf"
    digit: str


class SessionEnd(_Envelope):
    type: Literal["session.end"] = "session.end"
    reason: SessionEndReason
    duration_s: float = Field(ge=0.0)
    recording_url: str | None = None


PipelineToBrainMessage = Annotated[
    SessionStart | UtterancePartial | Utterance | AgentInterrupted | Dtmf | SessionEnd,
    Field(discriminator="type"),
]
_pipeline_to_brain_adapter: TypeAdapter[PipelineToBrainMessage] = TypeAdapter(
    PipelineToBrainMessage
)


# ---------------------------------------------------------------------------
# Brain -> Pipeline
# ---------------------------------------------------------------------------


class ReplyDelta(_Envelope):
    type: Literal["reply.delta"] = "reply.delta"
    turn_id: str
    text: str


class ReplyDone(_Envelope):
    type: Literal["reply.done"] = "reply.done"
    turn_id: str
    full_text: str
    action: Action
    language: Language


class PriorityUpdate(_Envelope):
    type: Literal["priority.update"] = "priority.update"
    score: int = Field(ge=0, le=100)
    level: Priority
    reason: str


class Escalate(_Envelope):
    type: Literal["escalate"] = "escalate"
    reason: str
    whisper_text: str


class SessionResult(_Envelope):
    type: Literal["session.result"] = "session.result"
    priority_level: Priority
    score: int = Field(ge=0, le=100)
    intent: Intent
    summary: str
    caller_name_guess: str | None = None
    callback_needed: bool
    callback_window: str | None = None
    reason: str


class BrainError(_Envelope):
    type: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool


BrainToPipelineMessage = Annotated[
    ReplyDelta | ReplyDone | PriorityUpdate | Escalate | SessionResult | BrainError,
    Field(discriminator="type"),
]
_brain_to_pipeline_adapter: TypeAdapter[BrainToPipelineMessage] = TypeAdapter(
    BrainToPipelineMessage
)


def parse_pipeline_message(raw: dict[str, Any]) -> PipelineToBrainMessage:
    """Parse a raw dict received by the brain from the pipeline.

    Raises UnknownMessageType for an unrecognized `type` so the brain can log and ignore it
    instead of crashing the session, per docs/HANDOFF.md §5.4.
    """
    if raw.get("type") not in _PIPELINE_TO_BRAIN_TYPES:
        raise UnknownMessageType(raw.get("type"))
    return _pipeline_to_brain_adapter.validate_python(raw)


def parse_brain_message(raw: dict[str, Any]) -> BrainToPipelineMessage:
    """Parse a raw dict received by the pipeline from the brain. See parse_pipeline_message."""
    if raw.get("type") not in _BRAIN_TO_PIPELINE_TYPES:
        raise UnknownMessageType(raw.get("type"))
    return _brain_to_pipeline_adapter.validate_python(raw)


_PIPELINE_TO_BRAIN_TYPES = {
    "session.start",
    "utterance.partial",
    "utterance",
    "agent.interrupted",
    "dtmf",
    "session.end",
}
_BRAIN_TO_PIPELINE_TYPES = {
    "reply.delta",
    "reply.done",
    "priority.update",
    "escalate",
    "session.result",
    "error",
}
