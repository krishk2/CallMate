from ..config import settings
from .base import LLMProvider, ReplyChunk
from .mock import MockLLMProvider


def create_llm_provider() -> LLMProvider:
    """The only place that branches on `LLM_PROVIDER`."""
    match settings.llm_provider:
        case "mock":
            return MockLLMProvider()
        case "anthropic":
            from .anthropic_provider import AnthropicProvider

            return AnthropicProvider()
        case "gemini":
            from .gemini_provider import GeminiProvider

            return GeminiProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


__all__ = ["LLMProvider", "ReplyChunk", "create_llm_provider"]
