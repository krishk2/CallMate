"""Intent classification, two stages (docs/HANDOFF.md §7.1.7): rules first (cheap, no I/O),
then an LLM call in strict JSON — run in parallel with the reply, never blocking it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from callmate_contracts.enums import Intent

from ..llm.base import LLMProvider
from .prompt_builder import fence_caller_text
from .prompt_templates import env

INTENT_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": [intent.value for intent in Intent]},
        "urgency": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
    "required": ["intent", "urgency", "reason"],
}

_KEYWORD_RULES: dict[Intent, set[str]] = {
    Intent.DELIVERY_LOGISTICS: {"delivery", "package", "courier", "parcel"},
    Intent.APPOINTMENT: {"appointment", "schedule a meeting", "reschedule", "time slot"},
    Intent.SALES_MARKETING: {"special offer", "discount", "subscription", "insurance policy"},
    Intent.SCAM_SUSPECTED: {"otp", "kyc", "verify your account", "account will be blocked"},
}


@dataclass(frozen=True)
class RuleClassification:
    intent: Intent | None
    matched_keyword: str | None


def classify_by_rules(
    *, caller_text: str, contact_relationship: str | None, repeat_calls_in_window: int
) -> RuleClassification:
    lowered = caller_text.lower()
    for intent, keywords in _KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in lowered:
                return RuleClassification(intent=intent, matched_keyword=keyword)

    if repeat_calls_in_window >= 3 and contact_relationship not in {"family", "friend", "work"}:
        return RuleClassification(intent=Intent.PERSONAL_URGENT, matched_keyword=None)
    if contact_relationship in {"family", "friend"}:
        return RuleClassification(intent=Intent.PERSONAL_CASUAL, matched_keyword=None)
    if contact_relationship == "work":
        return RuleClassification(intent=Intent.WORK, matched_keyword=None)

    return RuleClassification(intent=None, matched_keyword=None)


def render_classify_system_prompt() -> str:
    return env.get_template("classify_intent.j2").render(
        intent_labels=[intent.value for intent in Intent]
    ).strip()


async def classify_intent_with_llm(llm: LLMProvider, *, caller_text: str) -> dict[str, Any]:
    return await llm.classify(
        system_prompt=render_classify_system_prompt(),
        user_prompt=fence_caller_text(caller_text),
        schema=INTENT_CLASSIFY_SCHEMA,
    )
