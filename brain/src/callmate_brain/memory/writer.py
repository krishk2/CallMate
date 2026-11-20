"""Post-call: decide what to remember (docs/HANDOFF.md §7.1.4). Redact first; never store
anything on the user's never-share list — this is a second layer behind output_filter, which
already stops never-share content from being spoken during the call.
"""

from __future__ import annotations

from callmate_contracts.messages import SessionResult

from ..safety.redact import redact
from .embeddings import EmbeddingProvider
from .longterm import LongTermMemoryStore


async def write_post_call_memory(
    *,
    store: LongTermMemoryStore,
    embeddings: EmbeddingProvider,
    user_id: str,
    caller_number: str,
    result: SessionResult,
) -> str:
    safe_summary = redact(result.summary)
    embedding = await embeddings.embed(safe_summary, kind="passage")
    return await store.add(
        user_id, safe_summary, embedding, kind="summary", caller_number=caller_number
    )
