from ..config import settings
from .base import LLMProvider, ReplyChunk
from .mock import MockLLMProvider


def create_reply_llm_provider() -> LLMProvider:
    """The only place that branches on `REPLY_LLM_PROVIDER`. Handles stream_reply (live
    turns) and classify (intent) — both frequent, latency-sensitive calls.
    """
    match settings.reply_llm_provider:
        case "mock":
            return MockLLMProvider()
        case "groq":
            from .groq_provider import GroqProvider

            return GroqProvider()
    raise ValueError(f"Unknown REPLY_LLM_PROVIDER: {settings.reply_llm_provider}")


def create_summary_llm_provider() -> LLMProvider:
    """The only place that branches on `SUMMARY_LLM_PROVIDER`. Handles summarise — once per
    call, not latency-sensitive.
    """
    match settings.summary_llm_provider:
        case "mock":
            return MockLLMProvider()
        case "nvidia":
            from .nvidia_nim_provider import NvidiaNimProvider

            return NvidiaNimProvider()
    raise ValueError(f"Unknown SUMMARY_LLM_PROVIDER: {settings.summary_llm_provider}")


__all__ = [
    "LLMProvider",
    "ReplyChunk",
    "create_reply_llm_provider",
    "create_summary_llm_provider",
]
