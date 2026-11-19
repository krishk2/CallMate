#!/usr/bin/env python
"""Feed a recorded .ulaw file through the pipeline offline, against real STT/TTS and the
echo brain, to catch regressions without a live Twilio call (docs/HANDOFF.md §9.3, Week 6).

TODO: implement the frame-pacing loop (read 20ms mu-law frames from the fixture, call
`CallSession.handle_caller_audio` at real-time pace, capture `audio_out` frames to a .ulaw
file) once media/stream_ws.py and session/call_session.py are stable enough that regression
coverage here is worth the upkeep.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "ulaw_file", help="Path to a 8kHz mu-law recording, e.g. tests/fixtures/audio/*.ulaw"
    )
    parser.add_argument("--call-id", default="replay")
    args = parser.parse_args()
    raise NotImplementedError(f"replay_call.py: see TODO at top of module (args={args})")


if __name__ == "__main__":
    main()
