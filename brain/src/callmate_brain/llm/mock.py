"""Deterministic scripted LLM stand-in, so the rest of the brain can be developed and tested
with zero LLM provider/API key (LLM_PROVIDER=mock).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .base import LLMProvider, ReplyChunk


class MockLLMProvider(LLMProvider):
    def __init__(self, scripted_replies: list[str] | None = None) -> None:
        self._scripted = list(scripted_replies or ["Thanks for calling, I'll pass that on."])

    async def stream_reply(
        self, *, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[ReplyChunk]:
        text = self._scripted.pop(0) if self._scripted else "I'll pass that on."
        for word in text.split(" "):
            yield ReplyChunk(text=f"{word} ", is_final=False)
        yield ReplyChunk(text="", is_final=True)

    async def classify(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        return {"intent": "other", "urgency": 0.3, "reason": "mock classification"}

    async def summarise(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "priority_level": "normal",
            "score": 30,
            "intent": "other",
            "summary": "Mock summary — no real session content was analyzed.",
            "callback_needed": False,
            "reason": "mock_mode",
        }
