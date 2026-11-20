"""NVIDIA NIM: hosted inference for the not-latency-critical post-call summary
(docs/HANDOFF.md §1.3's former Sonnet role). OpenAI-compatible API.
"""

from __future__ import annotations

from ..config import settings
from .openai_compatible import OpenAICompatibleProvider


class NvidiaNimProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        super().__init__(
            api_key=api_key or settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            model=model or settings.summary_model,
        )
