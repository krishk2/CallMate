"""`/v1/calls/{call_id}/ws` (docs/HANDOFF.md §5): the brain side of the one WebSocket per call.
Pipeline is the client; this handler is the server. Ties together persona/tone, safety,
reasoning/prompt_builder + turn_engine + intent + priority, and memory for one call.
"""

from __future__ import annotations

import hmac
import itertools
import json
from datetime import UTC, datetime

import structlog
from callmate_contracts.enums import Action
from callmate_contracts.messages import (
    BrainToPipelineMessage,
    PriorityUpdate,
    ReplyDone,
    SessionStart,
    UnknownMessageType,
    Utterance,
    parse_pipeline_message,
)
from callmate_contracts.rest import UserSettings
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..config import settings
from ..llm import create_reply_llm_provider, create_summary_llm_provider
from ..llm.base import LLMProvider
from ..memory.embeddings import EmbeddingProvider, create_embedding_provider
from ..memory.profile import UserProfile
from ..memory.repeat_calls import create_repeat_call_tracker
from ..memory.working import WorkingMemory
from ..memory.writer import write_post_call_memory
from ..persona.examples import retrieve_style_examples
from ..persona.tone import build_tone_directives
from ..reasoning.intent import classify_by_rules, classify_intent_with_llm
from ..reasoning.priority import PriorityInputs, score_call
from ..reasoning.prompt_builder import build_system_prompt
from ..reasoning.summariser import summarise_call
from ..reasoning.turn_engine import generate_reply
from ..safety.guardrails import build_guardrail_directive
from ..safety.injection import SAFE_REFUSAL_REPLY, is_injection_attempt
from ..storage import get_session
from ..storage.repositories import (
    SqlCallHistoryRepository,
    SqlContactRepository,
    SqlLongTermMemoryStore,
    SqlProfileRepository,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


async def _load_profile_or_default(user_id: str) -> UserProfile:
    async with get_session() as db:
        try:
            return await SqlProfileRepository(db).get(user_id)
        except LookupError:
            logger.warning("no_profile_row_using_defaults", user_id=user_id)
            return UserProfile(
                user_id=user_id,
                first_name="the user",
                pronouns="they/them",
                languages=["en-IN"],
                availability_text="",
                settings=UserSettings(),
            )


async def _run_turn(
    *,
    reply_llm: LLMProvider,
    embeddings: EmbeddingProvider,
    working_memory: WorkingMemory,
    session_start: SessionStart,
    utterance: Utterance,
    contact_relationship: str | None,
    repeat_calls_in_window: int,
    next_seq,
    send,
) -> None:
    turn_id = f"turn-{next_seq()}"

    if is_injection_attempt(utterance.text):
        logger.warning("prompt_injection_detected", call_id=session_start.call_id)
        working_memory.add_agent_turn(SAFE_REFUSAL_REPLY)
        await send(
            ReplyDone(
                call_id=session_start.call_id,
                seq=next_seq(),
                turn_id=turn_id,
                full_text=SAFE_REFUSAL_REPLY,
                action=Action.CONTINUE,
                language=utterance.language,
            )
        )
        return

    profile = await _load_profile_or_default(session_start.user_id)
    tone_directives = build_tone_directives(
        profile.settings.tone, caller_is_known=contact_relationship is not None
    )
    guardrail_directive = build_guardrail_directive(profile.settings.never_share or None)
    system_prompt = build_system_prompt(
        user_first_name=profile.first_name,
        tone_directives=tone_directives,
        guardrail_directive=guardrail_directive,
    )

    async with get_session() as db:
        memory_store = SqlLongTermMemoryStore(db)
        query_embedding = await embeddings.embed(utterance.text)
        retrieved = await memory_store.search(
            session_start.user_id,
            query_embedding,
            top_k=settings.retrieval_top_k,
            caller_number=session_start.caller_number,
        )
        style_examples = await retrieve_style_examples(
            memory_store, embeddings, user_id=session_start.user_id, caller_text=utterance.text
        )

    full_reply = ""
    async for out_message in generate_reply(
        llm=reply_llm,
        system_prompt=system_prompt,
        retrieved_memories=[memory.content for memory in retrieved] + style_examples,
        recent_turns=working_memory.recent(6),
        caller_text=utterance.text,
        call_id=session_start.call_id,
        turn_id=turn_id,
        next_seq=next_seq,
        language=utterance.language,
    ):
        if out_message.type == "reply.done":
            full_reply = out_message.full_text
        await send(out_message)
    working_memory.add_agent_turn(full_reply)

    rule_hit = classify_by_rules(
        caller_text=utterance.text,
        contact_relationship=contact_relationship,
        repeat_calls_in_window=repeat_calls_in_window,
    )
    llm_classification = await classify_intent_with_llm(reply_llm, caller_text=utterance.text)
    priority = score_call(
        PriorityInputs(
            relationship=contact_relationship,
            repeat_calls_in_window=repeat_calls_in_window,
            caller_text=utterance.text,
            llm_urgency=float(llm_classification.get("urgency", 0.0)),
            spam_signal=rule_hit.intent is not None and rule_hit.intent.value == "scam_suspected",
        )
    )
    await send(
        PriorityUpdate(
            call_id=session_start.call_id,
            seq=next_seq(),
            score=priority.score,
            level=priority.level,
            reason=priority.reason,
        )
    )


@router.websocket("/v1/calls/{call_id}/ws")
async def calls_ws(websocket: WebSocket, call_id: str) -> None:
    # Pipeline's RemoteBrainClient sends this (brain_client/client.py), but nothing here was
    # ever checking it — anyone who found this URL could drive a fake call session with no
    # auth at all. Reject before accept() so an unauthorized client never gets a connection.
    expected = f"Bearer {settings.service_token}"
    if not hmac.compare_digest(websocket.headers.get("authorization", ""), expected):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    seq_counter = itertools.count(1)

    def next_seq() -> int:
        return next(seq_counter)

    async def send(message: BrainToPipelineMessage) -> None:
        await websocket.send_text(message.model_dump_json())

    reply_llm = create_reply_llm_provider()
    summary_llm = create_summary_llm_provider()
    embeddings = create_embedding_provider()
    working_memory = WorkingMemory()
    session_start: SessionStart | None = None
    contact_relationship: str | None = None
    repeat_calls_in_window = 0
    call_started_at: datetime | None = None
    repeat_call_tracker = create_repeat_call_tracker()

    try:
        async for raw in websocket.iter_text():
            try:
                message = parse_pipeline_message(json.loads(raw))
            except UnknownMessageType as exc:
                logger.warning("ignoring unknown pipeline message type %r", exc.type_value)
                continue

            if message.type == "session.start":
                session_start = message
                call_started_at = datetime.now(UTC)
                async with get_session() as db:
                    context = await SqlContactRepository(db).call_context(
                        message.user_id, message.caller_number
                    )
                contact_relationship = context.relationship
                repeat_calls_in_window = await repeat_call_tracker.record_and_count(
                    message.user_id, message.caller_number
                )

            elif message.type == "utterance" and session_start is not None:
                working_memory.add_caller_turn(message.text)
                await _run_turn(
                    reply_llm=reply_llm,
                    embeddings=embeddings,
                    working_memory=working_memory,
                    session_start=session_start,
                    utterance=message,
                    contact_relationship=contact_relationship,
                    repeat_calls_in_window=repeat_calls_in_window,
                    next_seq=next_seq,
                    send=send,
                )

            elif message.type == "agent.interrupted":
                working_memory.trim_last_agent_turn(message.spoken_text)

            elif message.type == "session.end" and session_start is not None:
                profile = await _load_profile_or_default(session_start.user_id)
                result = await summarise_call(
                    summary_llm,
                    call_id=call_id,
                    seq=next_seq(),
                    user_first_name=profile.first_name,
                    transcript=working_memory.transcript(),
                )
                # A failure saving the memory must never swallow the session.result the
                # pipeline (and caller) are waiting on — that's a side effect, not the
                # response. Isolate it so it can't crash the WS handler before `send` below.
                try:
                    async with get_session() as db:
                        await write_post_call_memory(
                            store=SqlLongTermMemoryStore(db),
                            embeddings=embeddings,
                            user_id=session_start.user_id,
                            caller_number=session_start.caller_number,
                            result=result,
                        )
                except Exception:
                    logger.warning("write_post_call_memory_failed", call_id=call_id, exc_info=True)
                # Same isolation as the memory write above — GET /v1/users/{id}/calls and
                # GET /v1/calls/{id} read this; previously nothing ever wrote to it at all.
                try:
                    async with get_session() as db:
                        await SqlCallHistoryRepository(db).add_call(
                            call_id=call_id,
                            user_id=session_start.user_id,
                            caller_number=session_start.caller_number,
                            started_at=call_started_at or datetime.now(UTC),
                            duration_s=message.duration_s,
                            result=result,
                        )
                except Exception:
                    logger.warning("save_call_history_failed", call_id=call_id, exc_info=True)
                await send(result)
                break
    except WebSocketDisconnect:
        logger.info("brain_session_disconnected", call_id=call_id)
