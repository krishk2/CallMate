from ..config import settings
from .base import TTSChunk, TTSProvider
from .mock import MockTTSProvider


def create_tts_provider() -> TTSProvider:
    """The only place that branches on `TTS_PROVIDER`."""
    match settings.tts_provider:
        case "mock":
            return MockTTSProvider()
        case "elevenlabs":
            from .elevenlabs import ElevenLabsProvider

            return ElevenLabsProvider()
        case "google":
            from .google_tts import GoogleTTSProvider

            return GoogleTTSProvider()
    raise ValueError(f"Unknown TTS_PROVIDER: {settings.tts_provider}")


__all__ = ["TTSChunk", "TTSProvider", "create_tts_provider"]
