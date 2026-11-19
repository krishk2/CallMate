"""Outbound audio to Twilio's Media Streams WS, with `mark` tracking so the session knows
exactly what the caller heard before a barge-in (docs/HANDOFF.md §6.1.5).
"""

from __future__ import annotations

import base64
import itertools
from collections.abc import Awaitable, Callable
from typing import Any

SendJSON = Callable[[dict[str, Any]], Awaitable[None]]


class PlaybackQueue:
    def __init__(self, stream_sid: str, send_json: SendJSON) -> None:
        self._stream_sid = stream_sid
        self._send_json = send_json
        self._mark_ids = itertools.count(1)
        self._pending_marks: dict[str, str] = {}  # mark name -> text spoken up to that mark

    async def send_frame(self, ulaw_frame: bytes) -> None:
        await self._send_json(
            {
                "event": "media",
                "streamSid": self._stream_sid,
                "media": {"payload": base64.b64encode(ulaw_frame).decode()},
            }
        )

    async def send_mark(self, spoken_so_far: str) -> str:
        name = f"mark-{next(self._mark_ids)}"
        self._pending_marks[name] = spoken_so_far
        await self._send_json(
            {"event": "mark", "streamSid": self._stream_sid, "mark": {"name": name}}
        )
        return name

    def resolve_mark(self, name: str) -> str | None:
        """Call when Twilio's `mark` event echoes back; returns what had actually played."""
        return self._pending_marks.pop(name, None)

    async def clear(self) -> None:
        self._pending_marks.clear()
        await self._send_json({"event": "clear", "streamSid": self._stream_sid})
