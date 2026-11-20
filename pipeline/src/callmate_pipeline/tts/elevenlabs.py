"""ElevenLabs streaming TTS (Flash-class model, `ulaw_8000` output — no resampling needed),
using an Instant Voice Clone made only from the user's own consented samples
(docs/HANDOFF.md §8 — never clone a caller's voice). Implemented directly against
ElevenLabs' streaming WebSocket API (not their SDK, to avoid the extra dependency).

One WebSocket connection per `synthesize()` call (one per sentence/clause), not a
connection held open across the whole call — simpler and correct, at the cost of a fresh
handshake per sentence. TODO: if `tts_first_byte` latency (docs/HANDOFF.md §6.1.13) turns out
to be dominated by handshake overhead, switch to one persistent connection per call, fed
incrementally — ElevenLabs' protocol supports that, it's just more state to manage here.
"""

from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator

import websockets

from ..config import settings
from .base import TTSChunk, TTSProvider

_MODEL_ID = "eleven_flash_v2_5"


class ElevenLabsProvider(TTSProvider):
    def __init__(self, api_key: str | None = None, voice_id: str | None = None) -> None:
        self._api_key = api_key or settings.elevenlabs_api_key
        self._voice_id = voice_id or settings.elevenlabs_voice_id
        self._cancelled = False

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        self._cancelled = False
        url = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}/stream-input"
            f"?model_id={_MODEL_ID}&output_format=ulaw_8000"
        )
        async with websockets.connect(
            url, additional_headers={"xi-api-key": self._api_key}
        ) as ws:
            await ws.send(
                json.dumps(
                    {"text": " ", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
                )
            )
            await ws.send(json.dumps({"text": text}))
            await ws.send(json.dumps({"text": ""}))

            async for raw in ws:
                if self._cancelled:
                    return
                message = json.loads(raw)
                audio_b64 = message.get("audio")
                is_final = bool(message.get("isFinal"))
                if audio_b64:
                    yield TTSChunk(audio=base64.b64decode(audio_b64), is_final=is_final)
                if is_final:
                    return

    async def cancel(self) -> None:
        self._cancelled = True
