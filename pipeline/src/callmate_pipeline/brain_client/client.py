"""What call_session.py depends on to talk to the brain (dependency inversion): the protocol
below, never a concrete WebSocket client. `RemoteBrainClient` is the real implementation;
`echo_brain.EchoBrainClient` is a local stand-in for BRAIN_MODE=echo (docs/HANDOFF.md §9.2).
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

import websockets
from callmate_contracts.messages import (
    AgentInterrupted,
    BrainToPipelineMessage,
    SessionEnd,
    SessionResult,
    SessionStart,
    UnknownMessageType,
    Utterance,
    parse_brain_message,
)

from ..config import settings

logger = logging.getLogger(__name__)


class BrainClient(ABC):
    @abstractmethod
    async def start_session(self, start: SessionStart) -> None: ...

    @abstractmethod
    async def send_utterance(self, utterance: Utterance) -> None: ...

    @abstractmethod
    async def send_agent_interrupted(self, interrupted: AgentInterrupted) -> None: ...

    @abstractmethod
    def replies(self) -> AsyncIterator[BrainToPipelineMessage]:
        """reply.delta / reply.done / priority.update / escalate, in arrival order.
        session.result is returned by end_session instead of appearing here."""

    @abstractmethod
    async def end_session(self, end: SessionEnd) -> SessionResult: ...

    @abstractmethod
    async def close(self) -> None: ...


class RemoteBrainClient(BrainClient):
    """wss://.../v1/calls/{call_id}/ws, bearer-authenticated (docs/HANDOFF.md §5)."""

    def __init__(
        self, call_id: str, ws_url: str | None = None, service_token: str | None = None
    ) -> None:
        self._ws_url = f"{(ws_url or settings.brain_ws_url).rstrip('/')}/{call_id}/ws"
        self._service_token = service_token or settings.service_token
        self._ws: Any = None

    async def _connect(self) -> Any:
        if self._ws is None:
            self._ws = await websockets.connect(
                self._ws_url,
                additional_headers={"Authorization": f"Bearer {self._service_token}"},
            )
        return self._ws

    async def _send(
        self, message: SessionStart | Utterance | AgentInterrupted | SessionEnd
    ) -> None:
        ws = await self._connect()
        await ws.send(message.model_dump_json())

    async def start_session(self, start: SessionStart) -> None:
        await self._send(start)

    async def send_utterance(self, utterance: Utterance) -> None:
        await self._send(utterance)

    async def send_agent_interrupted(self, interrupted: AgentInterrupted) -> None:
        await self._send(interrupted)

    async def replies(self) -> AsyncIterator[BrainToPipelineMessage]:
        ws = await self._connect()
        async for raw in ws:
            try:
                message = parse_brain_message(json.loads(raw))
            except UnknownMessageType as exc:
                logger.warning("ignoring unknown brain message type %r", exc.type_value)
                continue
            if message.type == "session.result":
                continue  # returned by end_session instead
            yield message

    async def end_session(self, end: SessionEnd) -> SessionResult:
        await self._send(end)
        ws = await self._connect()
        async for raw in ws:
            try:
                message = parse_brain_message(json.loads(raw))
            except UnknownMessageType:
                continue
            if message.type == "session.result":
                return message
        raise ConnectionError("brain closed the connection before sending session.result")

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
