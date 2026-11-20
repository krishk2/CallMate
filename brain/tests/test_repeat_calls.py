import pytest
from callmate_brain.memory.repeat_calls import (
    NullRepeatCallTracker,
    RedisRepeatCallTracker,
    create_repeat_call_tracker,
)


@pytest.mark.asyncio
async def test_null_tracker_always_returns_zero():
    tracker = NullRepeatCallTracker()
    assert await tracker.record_and_count("demo", "+919800000001") == 0
    assert await tracker.record_and_count("demo", "+919800000001") == 0


def test_factory_returns_null_when_redis_not_configured(monkeypatch):
    from callmate_brain.config import settings

    monkeypatch.setattr(settings, "redis_url", "")
    assert isinstance(create_repeat_call_tracker(), NullRepeatCallTracker)


def test_factory_returns_redis_tracker_when_configured(monkeypatch):
    from callmate_brain.config import settings

    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379")
    assert isinstance(create_repeat_call_tracker(), RedisRepeatCallTracker)
