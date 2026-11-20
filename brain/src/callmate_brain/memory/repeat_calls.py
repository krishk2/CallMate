"""Tracks repeat calls from the same number within a short window
(docs/HANDOFF.md §7.1.8's "repeat-call bonus"; demo scenario #7 — 3 calls in 10 minutes bumps
priority). Backed by Redis so the count survives across separate WebSocket connections (each
call is a brand new one — there was never anywhere this could have lived in-process) and
brain restarts. Falls back to a no-op when `REDIS_URL` isn't configured, matching the
hardcoded-zero behavior this replaces rather than breaking when Redis isn't set up.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class RepeatCallTracker(ABC):
    @abstractmethod
    async def record_and_count(self, user_id: str, caller_number: str) -> int:
        """Records this call against the window and returns how many *prior* calls from this
        number landed within it — not counting the call being recorded right now."""


class NullRepeatCallTracker(RepeatCallTracker):
    async def record_and_count(self, user_id: str, caller_number: str) -> int:
        return 0


class RedisRepeatCallTracker(RepeatCallTracker):
    def __init__(self, redis_url: str, window_s: int) -> None:
        import redis.asyncio as redis

        self._client = redis.from_url(redis_url)
        self._window_s = window_s

    async def record_and_count(self, user_id: str, caller_number: str) -> int:
        key = f"repeat_calls:{user_id}:{caller_number}"
        count = await self._client.incr(key)
        if count == 1:
            await self._client.expire(key, self._window_s)
        return count - 1


def create_repeat_call_tracker() -> RepeatCallTracker:
    from ..config import settings

    if not settings.redis_url:
        return NullRepeatCallTracker()
    return RedisRepeatCallTracker(settings.redis_url, settings.repeat_call_window_s)
