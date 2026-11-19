#!/usr/bin/env python
"""Loads golden/red-team transcripts and reports intent + priority accuracy
(docs/HANDOFF.md §7.1.12). Run manually/nightly, not on every PR (docs/HANDOFF.md §9.3).

Scores the rule-based layer (reasoning/intent.py's classify_by_rules, reasoning/priority.py's
score_call) and the injection detector — all pure functions, so this needs no LLM provider and
runs in milliseconds. TODO: once anthropic_provider.py exists, add an LLM-in-the-loop pass that
also measures safety-filter catch rate (safety/output_filter.py) and average first-token
latency, per the full metric set in docs/HANDOFF.md §7.2.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml
from callmate_brain.reasoning.intent import classify_by_rules
from callmate_brain.reasoning.priority import PriorityInputs, score_call
from callmate_brain.safety.injection import is_injection_attempt

_EVALS_DIR = Path(__file__).resolve().parent
_LEVELS = ["low", "normal", "important", "urgent"]


@dataclass(frozen=True)
class EvalCase:
    name: str
    caller_text: str
    expected_intent: str
    expected_priority_level: str
    contact_relationship: str | None = None
    repeat_calls_in_window: int = 0
    llm_urgency: float = 0.0
    spam_signal: bool = False
    expect_injection_detected: bool | None = None


def load_cases(directory: Path) -> list[EvalCase]:
    if not directory.is_dir():
        return []
    cases = []
    for path in sorted(directory.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text())
        cases.append(EvalCase(name=path.stem, **raw))
    return cases


def run(cases: list[EvalCase]) -> None:
    intent_correct = 0
    priority_exact = 0
    priority_within_one = 0
    urgent_total = 0
    urgent_recalled = 0
    injection_checks = 0
    injection_correct = 0

    for case in cases:
        rule_hit = classify_by_rules(
            caller_text=case.caller_text,
            contact_relationship=case.contact_relationship,
            repeat_calls_in_window=case.repeat_calls_in_window,
        )
        predicted_intent = rule_hit.intent.value if rule_hit.intent else "other"
        intent_correct += predicted_intent == case.expected_intent

        priority = score_call(
            PriorityInputs(
                relationship=case.contact_relationship,
                repeat_calls_in_window=case.repeat_calls_in_window,
                caller_text=case.caller_text,
                llm_urgency=case.llm_urgency,
                spam_signal=case.spam_signal,
            )
        )
        if case.expected_priority_level == "urgent":
            urgent_total += 1
            urgent_recalled += priority.level.value == "urgent"
        priority_exact += priority.level.value == case.expected_priority_level
        actual_idx = _LEVELS.index(priority.level.value)
        expected_idx = _LEVELS.index(case.expected_priority_level)
        priority_within_one += abs(actual_idx - expected_idx) <= 1

        if case.expect_injection_detected is not None:
            injection_checks += 1
            injection_correct += (
                is_injection_attempt(case.caller_text) == case.expect_injection_detected
            )

    total = len(cases) or 1
    print(f"cases: {len(cases)}")
    print(f"intent accuracy: {intent_correct / total:.0%}")
    print(f"priority exact: {priority_exact / total:.0%}")
    print(f"priority within one level: {priority_within_one / total:.0%}")
    if urgent_total:
        print(f"urgent recall: {urgent_recalled / urgent_total:.0%}")
    if injection_checks:
        print(f"injection detection accuracy: {injection_correct / injection_checks:.0%}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=["transcripts", "redteam", "all"], default="all")
    args = parser.parse_args()

    directories = []
    if args.set in ("transcripts", "all"):
        directories.append(_EVALS_DIR / "transcripts")
    if args.set in ("redteam", "all"):
        directories.append(_EVALS_DIR / "redteam")

    cases = [case for directory in directories for case in load_cases(directory)]
    if not cases:
        print("No eval cases yet — add YAML files under evals/transcripts/ and evals/redteam/.")
        return
    run(cases)


if __name__ == "__main__":
    main()
