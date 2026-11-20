"""Twilio Media Streams WebSocket handler: the only place that knows Twilio's wire format
(`connected`/`start`/`media`/`mark`/`stop`). Translates it to CallSession's plain
bytes-in/bytes-out interface, so CallSession itself needs no knowledge of Twilio.

TODO (docs/HANDOFF.md §6.1.5): exact-spoken-text barge-in needs `PlaybackQueue.send_mark`
called per TTS chunk sent and `resolve_mark` consulted here on `mark` echoes, to pass the real
`spoken_text` into `handle_barge_in` instead of "". Wire that up with the Week-4 barge-in work.
"""

from __future__ import annotations

import base64
import json
import time
from contextlib import AsyncExitStack

import structlog
from callmate_contracts.enums import CallMode, Language, SessionEndReason
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..brain_client import create_brain_client
from ..notify import send_call_summary_notifications
from ..session.call_session import CallSession
from ..session.state import CallState
from ..storage import get_session
from ..storage.repositories import SqlCallRepository
from ..stt import create_stt_provider
from ..tts import create_tts_provider
from .codec import ulaw_to_pcm16
from .playback import PlaybackQueue
from .vad import BargeInDetector, EnergyThresholdVAD

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.websocket("/media/{call_id}")
async def media_stream(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()
    playback: PlaybackQueue | None = None
    session: CallSession | None = None
    caller_number = ""
    caller_name: str | None = None
    started_at = time.monotonic()
    barge_in = BargeInDetector(EnergyThresholdVAD())
    db_stack = AsyncExitStack()

    async def audio_out(ulaw_frame: bytes) -> None:
        if playback is not None:
            await playback.send_frame(ulaw_frame)

    try:
        async for raw in websocket.iter_text():
            event = json.loads(raw)
            match event.get("event"):
                case "start":
                    stream_sid = event["start"]["streamSid"]
                    playback = PlaybackQueue(stream_sid, websocket.send_json)
                    custom = event["start"].get("customParameters", {})
                    caller_number = custom.get("caller_number", "")
                    caller_name = custom.get("caller_name") or None
                    db = await db_stack.enter_async_context(get_session())
                    session = CallSession(
                        call_id=call_id,
                        user_id=custom.get("user_id", ""),
                        caller_number=caller_number,
                        mode=CallMode(custom.get("mode", CallMode.SCREEN_UNKNOWN.value)),
                        stt=create_stt_provider(),
                        tts=create_tts_provider(),
                        brain=create_brain_client(call_id),
                        audio_out=audio_out,
                        language_hint=Language(custom.get("language_hint", Language.AUTO.value)),
                        call_repository=SqlCallRepository(db),
                    )
                    await session.start()
                case "media":
                    if session is None:
                        continue
                    ulaw_frame = base64.b64decode(event["media"]["payload"])
                    if session.state == CallState.SPEAKING:
                        if barge_in.feed(ulaw_to_pcm16(ulaw_frame)):
                            await session.handle_barge_in(spoken_text="")
                            if playback is not None:
                                await playback.clear()
                    else:
                        barge_in.reset()
                    await session.handle_caller_audio(ulaw_frame)
                case "stop":
                    logger.info("twilio_stop_event", call_id=call_id, raw=event)
                    break
                case other:
                    logger.info(
                        "unhandled_media_stream_event", call_id=call_id, event_type=other, raw=event
                    )
    except WebSocketDisconnect:
        logger.info("media_stream_disconnected", call_id=call_id)
    finally:
        if session is not None:
            result = await session.close(SessionEndReason.CALLER_HANGUP)
            await send_call_summary_notifications(
                caller_number=caller_number,
                caller_name=caller_name,
                result=result,
                duration_s=time.monotonic() - started_at,
            )
        await db_stack.aclose()
