"""Deepgram Nova-2 streaming STT (Telugu `language=te`, or `en-IN`). Implemented directly
against Deepgram's streaming WebSocket API (not the `deepgram-sdk`, to avoid the extra
dependency for a protocol this small) using `endpointing` + `utterance_end_ms` for
turn-taking, since Nova has no native turn detection the way Flux does
(docs/HANDOFF.md §6.1.3/§6.1.4).
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
from .base import STTProvider, STTResult

logger = structlog.get_logger(__name__)

_DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"


def _build_query(language_hint: str, keyterms: list[str] | None) -> str:
    params: list[tuple[str, str]] = [
        ("model", "nova-2"),
        ("encoding", "mulaw"),
        ("sample_rate", "8000"),
        ("punctuate", "true"),
        ("interim_results", "true"),
        ("endpointing", "300"),
        ("utterance_end_ms", "1000"),
    ]
    if language_hint == "auto":
        params.append(("detect_language", "true"))
    else:
        params.append(("language", language_hint))
    for keyterm in keyterms or []:
        params.append(("keyterm", keyterm))
    return urllib.parse.urlencode(params)


class DeepgramNovaProvider(STTProvider):
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
        if self._ws is not None:
            await self._ws.send(chunk)

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
                if message.get("type") != "Results":
                    continue
                alternatives = message.get("channel", {}).get("alternatives", [])
                if not alternatives:
                    continue
                text = alternatives[0].get("transcript", "")
                if not text:
                    continue
                is_final = bool(message.get("is_final") or message.get("speech_final"))
                await self._queue.put(
                    STTResult(
                        text=text,
                        confidence=alternatives[0].get("confidence", 0.0),
                        is_final=is_final,
                    )
                )
        except websockets.exceptions.ConnectionClosed:
            logger.info("deepgram_connection_closed")
        except asyncio.CancelledError:
            pass
