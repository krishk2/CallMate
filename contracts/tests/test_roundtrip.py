from datetime import datetime

import pytest
from callmate_contracts.enums import Action, CallMode, Intent, Language, Priority, SessionEndReason
from callmate_contracts.messages import (
    BrainToPipelineMessage,
    Escalate,
    PipelineToBrainMessage,
    PriorityUpdate,
    ReplyDone,
    SessionEnd,
    SessionResult,
    SessionStart,
    UnknownMessageType,
    parse_brain_message,
    parse_pipeline_message,
)
from pydantic import ValidationError

PIPELINE_MESSAGES = [
    SessionStart(
        call_id="c1", seq=1, user_id="u1", caller_number="+919800000000", mode=CallMode.AWAY
    ),
    SessionEnd(call_id="c1", seq=99, reason=SessionEndReason.CALLER_HANGUP, duration_s=42.0),
]

BRAIN_MESSAGES = [
    ReplyDone(
        call_id="c1",
        seq=2,
        turn_id="t1",
        full_text="One moment, I'll pass that on.",
        action=Action.TAKE_MESSAGE,
        language=Language.EN_IN,
    ),
    PriorityUpdate(
        call_id="c1", seq=3, score=85, level=Priority.URGENT, reason="emergency keyword"
    ),
    Escalate(call_id="c1", seq=4, reason="urgent", whisper_text="Your brother may need you."),
    SessionResult(
        call_id="c1",
        seq=100,
        priority_level=Priority.URGENT,
        score=85,
        intent=Intent.PERSONAL_URGENT,
        summary="Caller says your brother was in a minor accident.",
        callback_needed=True,
        reason="emergency keyword",
    ),
]


@pytest.mark.parametrize("message", PIPELINE_MESSAGES)
def test_pipeline_message_roundtrip(message: PipelineToBrainMessage) -> None:
    raw = message.model_dump(mode="json")
    parsed = parse_pipeline_message(raw)
    assert parsed == message


@pytest.mark.parametrize("message", BRAIN_MESSAGES)
def test_brain_message_roundtrip(message: BrainToPipelineMessage) -> None:
    raw = message.model_dump(mode="json")
    parsed = parse_brain_message(raw)
    assert parsed == message


def test_unknown_pipeline_type_is_ignorable() -> None:
    with pytest.raises(UnknownMessageType):
        parse_pipeline_message({"type": "future.message", "call_id": "c1", "seq": 1})


def test_unknown_brain_type_is_ignorable() -> None:
    with pytest.raises(UnknownMessageType):
        parse_brain_message({"type": "future.message", "call_id": "c1", "seq": 1})


def test_envelope_defaults_protocol_version() -> None:
    msg = SessionStart(call_id="c1", seq=1, user_id="u1", caller_number="+91", mode=CallMode.AWAY)
    assert msg.v == "1.0"
    assert isinstance(msg.ts, datetime)
    assert msg.ts.tzinfo is not None


def test_utterance_requires_explicit_timestamps() -> None:
    with pytest.raises(ValidationError):
        parse_pipeline_message(
            {
                "type": "utterance",
                "call_id": "c1",
                "seq": 5,
                "text": "hello",
                "language": "en-IN",
                "confidence": 0.9,
            }
        )
