"""Deepgram Flux streaming STT — default for English/Hindi, chosen for native turn
detection (docs/HANDOFF.md §1.2/§6.1.3): unlike Nova, Flux decides end-of-turn itself via
`TurnInfo` events, so no `endpointing`/`utterance_end_ms` tuning is needed.

Flux uses a different API version and audio format than Nova/v1 (confirmed against
developers.deepgram.com/docs/flux/quickstart — verify again if this starts rejecting
connections, their naming has moved before): `/v2/listen`, `linear16` at 16kHz, not
`/v1/listen`'s `mulaw`/8kHz. Twilio only ever gives us mu-law 8kHz, so this provider converts
every chunk (codec.ulaw_to_pcm16 + resample_pcm16) before sending it on.
"""

from __future__ import annotations

import asyncio
import json
import urllib.parse
from collections.abc import AsyncIterator
from typing import Any

import structlog
import websockets

from ..config import settings
from ..media.codec import resample_pcm16, ulaw_to_pcm16
from .base import STTProvider, STTResult

logger = structlog.get_logger(__name__)

_DEEPGRAM_URL = "wss://api.deepgram.com/v2/listen"
_SOURCE_RATE = 8000
_TARGET_RATE = 16000


def _build_query(language_hint: str, keyterms: list[str] | None) -> str:
    model = "flux-general-en" if language_hint in ("auto", "en", "en-IN") else "flux-general-multi"
    params: list[tuple[str, str]] = [
        ("model", model),
        ("encoding", "linear16"),
        ("sample_rate", str(_TARGET_RATE)),
    ]
    for keyterm in keyterms or []:
        params.append(("keyterm", keyterm))
    return urllib.parse.urlencode(params)


class DeepgramFluxProvider(STTProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.deepgram_api_key
        self._ws: Any = None
        self._queue: asyncio.Queue[STTResult] = asyncio.Queue()
        self._receive_task: asyncio.Task[None] | None = None

    async def start(self, *, language_hint: str, keyterms: list[str] | None = None) -> None:
        url = f"{_DEEPGRAM_URL}?{_build_query(language_hint, keyterms)}"
        self._ws = await websockets.connect(
            url, additional_headers={"Authorization": f"Token {self._api_key}"}
        )
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def send_audio(self, chunk: bytes) -> None:
        if self._ws is None:
            return
        pcm_8k = ulaw_to_pcm16(chunk)
        pcm_16k = resample_pcm16(pcm_8k, _SOURCE_RATE, _TARGET_RATE)
        await self._ws.send(pcm_16k)

    async def results(self) -> AsyncIterator[STTResult]:
        while True:
            yield await self._queue.get()

    async def close(self) -> None:
        if self._receive_task is not None:
            self._receive_task.cancel()
            self._receive_task = None
        if self._ws is not None:
            await self._ws.send(json.dumps({"type": "CloseStream"}))
            await self._ws.close()
            self._ws = None

    async def _receive_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                message = json.loads(raw)
                if message.get("type") != "TurnInfo":
                    continue
                text = message.get("transcript", "")
                if not text:
                    continue
                event = message.get("event")
                is_final = event == "EndOfTurn"
                await self._queue.put(
                    STTResult(
                        text=text,
                        confidence=message.get("end_of_turn_confidence", 0.0),
                        is_final=is_final,
                    )
                )
        except websockets.exceptions.ConnectionClosed:
            logger.info("deepgram_connection_closed")
        except asyncio.CancelledError:
            pass
