from ..config import settings
from .client import BrainClient, RemoteBrainClient
from .echo_brain import EchoBrainClient


def create_brain_client(call_id: str) -> BrainClient:
    """The only place that branches on `BRAIN_MODE`."""
    match settings.brain_mode:
        case "echo":
            return EchoBrainClient()
        case "remote":
            return RemoteBrainClient(call_id)
    raise ValueError(f"Unknown BRAIN_MODE: {settings.brain_mode}")


__all__ = ["BrainClient", "RemoteBrainClient", "EchoBrainClient", "create_brain_client"]
