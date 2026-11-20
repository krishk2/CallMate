"""On session.end, produce the structured session.result (docs/HANDOFF.md §7.1.9): validated
by Pydantic, retry once on invalid JSON, then fall back to a rules-only summary so the
pipeline always gets *some* session.result within its 10s budget (docs/HANDOFF.md §5.2).
"""

from __future__ import annotations

import structlog
from callmate_contracts.enums import Intent, Priority
from callmate_contracts.messages import SessionResult
from pydantic import ValidationError

from ..llm.base import LLMProvider
from .prompt_templates import env

logger = structlog.get_logger(__name__)

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "priority_level": {"type": "string", "enum": [p.value for p in Priority]},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "intent": {"type": "string", "enum": [i.value for i in Intent]},
        "summary": {"type": "string"},
        "callback_needed": {"type": "boolean"},
        "callback_window": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["priority_level", "score", "intent", "summary", "callback_needed", "reason"],
}


def _rules_only_fallback(call_id: str, seq: int) -> SessionResult:
    return SessionResult(
        call_id=call_id,
        seq=seq,
        priority_level=Priority.NORMAL,
        score=30,
        intent=Intent.OTHER,
        summary="Summary unavailable; the LLM did not return valid structured output.",
        callback_needed=False,
        reason="summariser_fallback",
    )


def render_summarise_system_prompt(user_first_name: str) -> str:
    return (
        env.get_template("summarise_call.j2")
        .render(
            user_first_name=user_first_name,
            priority_levels=[p.value for p in Priority],
            intent_labels=[i.value for i in Intent],
        )
        .strip()
    )


async def summarise_call(
    llm: LLMProvider, *, call_id: str, seq: int, user_first_name: str, transcript: str
) -> SessionResult:
    system_prompt = render_summarise_system_prompt(user_first_name)
    for attempt in range(2):
        raw = await llm.summarise(
            system_prompt=system_prompt, user_prompt=transcript, schema=SUMMARY_SCHEMA
        )
        try:
            return SessionResult(call_id=call_id, seq=seq, **raw)
        except (ValidationError, TypeError) as exc:
            logger.warning(
                "summary_json_invalid", attempt=attempt, call_id=call_id, raw=raw, error=str(exc)
            )
    return _rules_only_fallback(call_id, seq)
