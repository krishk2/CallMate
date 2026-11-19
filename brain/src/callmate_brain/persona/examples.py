"""Retrieves few-shot user style examples for the live prompt (docs/HANDOFF.md §7.1.2),
reusing the same long-term store and embedding provider as call-summary memory, filtered to
`kind="style_example"`.
"""

from __future__ import annotations

from ..memory.embeddings import EmbeddingProvider
from ..memory.longterm import LongTermMemoryStore


async def retrieve_style_examples(
    store: LongTermMemoryStore,
    embeddings: EmbeddingProvider,
    *,
    user_id: str,
    caller_text: str,
    top_k: int = 3,
) -> list[str]:
    query_embedding = await embeddings.embed(caller_text)
    results = await store.search(user_id, query_embedding, top_k=top_k)
    return [result.content for result in results]
