#!/usr/bin/env python
"""Prints p50/p95 per latency stage from persisted spans (docs/HANDOFF.md §6.1.13).

Owned by Antigravity (ANTIGRAVITY_HANDOFF.md §1.4) — pure reporting over
`storage.models.LatencySpanRow`, no call-path code. Left as a stub here so the script exists
and the CLI shape is settled; fill in the query + percentile math.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError("latency_report.py: owned by Antigravity, see module docstring")


if __name__ == "__main__":
    main()
