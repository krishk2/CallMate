"""Per-turn latency spans (docs/HANDOFF.md §6.1.13). `scripts/latency_report.py` reads
persisted spans and prints p50/p95 per stage — this module only records them.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

STAGES = (
    "eot_detected",
    "final_transcript",
    "brain_first_token",
    "tts_first_byte",
    "first_audio_sent",
)


@dataclass
class TurnSpan:
    turn_id: str
    call_id: str
    marks: dict[str, float] = field(default_factory=dict)

    def mark(self, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError(f"Unknown latency stage: {stage!r}, expected one of {STAGES}")
        self.marks[stage] = time.monotonic()

    def duration_ms(self, start_stage: str, end_stage: str) -> float | None:
        if start_stage not in self.marks or end_stage not in self.marks:
            return None
        return (self.marks[end_stage] - self.marks[start_stage]) * 1000


class LatencyRecorder:
    """In-process sink for TurnSpans for one call. Owner (call_session.py) is responsible for
    persisting finished spans to `storage/` so latency_report.py can aggregate across calls.
    """

    def __init__(self) -> None:
        self._spans: list[TurnSpan] = []

    def new_span(self, turn_id: str, call_id: str) -> TurnSpan:
        span = TurnSpan(turn_id=turn_id, call_id=call_id)
        self._spans.append(span)
        return span

    def spans(self) -> list[TurnSpan]:
        return list(self._spans)
