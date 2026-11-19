"""Hybrid priority scoring, 0-100 (docs/HANDOFF.md §7.1.8, §8): relationship weight +
repeat-call bonus + LLM urgency - spam penalty, with emergency keywords forcing Urgent
outright. Weights live in config.py so they can be tuned from eval results without a
code change (docs/HANDOFF.md §10, Week 6-7).
"""

from __future__ import annotations

from dataclasses import dataclass

from callmate_contracts.enums import Priority

from ..config import settings

# TODO (docs/HANDOFF.md §7.1.8): add real Hindi/Telugu equivalents once red-team testing
# with native speakers is underway — these English terms are a placeholder.
EMERGENCY_KEYWORDS = {"hospital", "accident", "police", "ambulance", "emergency"}


@dataclass(frozen=True)
class PriorityInputs:
    relationship: str | None
    repeat_calls_in_window: int
    caller_text: str
    llm_urgency: float  # 0.0-1.0, from reasoning/intent.py's LLM classification stage
    spam_signal: bool


@dataclass(frozen=True)
class PriorityResult:
    score: int
    level: Priority
    reason: str
    forced_urgent: bool


def _has_emergency_keyword(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in EMERGENCY_KEYWORDS)


def score_call(inputs: PriorityInputs) -> PriorityResult:
    if _has_emergency_keyword(inputs.caller_text):
        return PriorityResult(
            score=100, level=Priority.URGENT, reason="emergency keyword", forced_urgent=True
        )

    relationship_weight = settings.priority_relationship_weights.get(inputs.relationship or "", 0)
    repeat_bonus = min(inputs.repeat_calls_in_window, 3) * settings.priority_repeat_call_bonus
    urgency_component = round(inputs.llm_urgency * settings.priority_llm_urgency_weight)
    spam_penalty = settings.priority_spam_penalty if inputs.spam_signal else 0

    score = max(0, min(100, relationship_weight + repeat_bonus + urgency_component - spam_penalty))

    if score >= settings.priority_urgent_threshold:
        level = Priority.URGENT
    elif score >= settings.priority_important_threshold:
        level = Priority.IMPORTANT
    elif score >= settings.priority_normal_threshold:
        level = Priority.NORMAL
    else:
        level = Priority.LOW

    return PriorityResult(
        score=score,
        level=level,
        reason=(
            f"relationship=+{relationship_weight} repeat=+{repeat_bonus} "
            f"urgency=+{urgency_component} spam=-{spam_penalty}"
        ),
        forced_urgent=False,
    )
