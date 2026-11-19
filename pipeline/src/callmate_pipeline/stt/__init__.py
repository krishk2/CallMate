from ..config import settings
from .base import STTProvider, STTResult
from .mock import MockSTTProvider


def create_stt_provider() -> STTProvider:
    """The only place that branches on `STT_PROVIDER`. Everything else depends on
    `STTProvider` (dependency inversion) and never sees this switch.
    """
    match settings.stt_provider:
        case "mock":
            return MockSTTProvider()
        case "deepgram_flux":
            from .deepgram_flux import DeepgramFluxProvider

            return DeepgramFluxProvider()
        case "deepgram_nova":
            from .deepgram_nova import DeepgramNovaProvider

            return DeepgramNovaProvider()
        case "google":
            from .google_v2 import GoogleSTTProvider

            return GoogleSTTProvider()
    raise ValueError(f"Unknown STT_PROVIDER: {settings.stt_provider}")


__all__ = ["STTProvider", "STTResult", "create_stt_provider"]
