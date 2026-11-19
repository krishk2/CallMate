#!/usr/bin/env python
"""Text-only call simulator: type as the caller, see the brain's streamed replies, priority
updates, and final session.result (docs/HANDOFF.md §9.2).

Owned by Antigravity (ANTIGRAVITY_HANDOFF.md §1.1). Talks to the brain over the same
WebSocket contract the pipeline uses (`contracts/`) — connect to
`ws://localhost:8001/v1/calls/{call_id}/ws`, send a session.start, then an utterance per
line typed, print reply.delta/reply.done/priority.update as they arrive, and send
session.end on Ctrl-D.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="demo")
    parser.add_argument("--caller", default="+919800000000")
    args = parser.parse_args()
    raise NotImplementedError(
        f"sim_call.py: owned by Antigravity, see module docstring (args={args})"
    )


if __name__ == "__main__":
    main()
