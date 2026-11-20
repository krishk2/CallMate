"""Shared implementation for any OpenAI-compatible chat completions API. Groq and NVIDIA NIM
both expose this shape — they differ only in base_url/api_key/model, so neither provider
needs its own HTTP logic.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import structlog
from openai import AsyncOpenAI

from .base import LLMProvider, ReplyChunk

logger = structlog.get_logger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def stream_reply(
        self, *, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[ReplyChunk]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system_prompt}, *messages],
            stream=True,
        )
        async for event in stream:
            delta = event.choices[0].delta.content or ""
            if delta:
                yield ReplyChunk(text=delta, is_final=False)
        yield ReplyChunk(text="", is_final=True)

    async def classify(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._json_completion(system_prompt, user_prompt)

    async def summarise(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._json_completion(system_prompt, user_prompt)

    async def _json_completion(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Best-effort JSON mode. Returns {} on any failure (unsupported response_format,
        network error, invalid JSON) rather than raising — callers (summariser.py's
        retry+fallback, intent.py's rule fallback) already handle an empty/invalid result.
        """
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception:
            logger.warning("llm_json_completion_failed", model=self._model)
            return {}
