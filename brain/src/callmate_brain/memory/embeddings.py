"""Embedding provider protocol. `reasoning`/`memory` code depends on `EmbeddingProvider`,
never on a concrete embedding model.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

EMBEDDING_DIM = 32  # must match storage/models.py MemoryRow.embedding's Vector() dimension


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...


class LocalHashEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free stand-in: hashes text into a fixed-size vector with no
    semantic meaning. Enough to exercise the pgvector plumbing and pass tests.
    TODO (docs/HANDOFF.md §1.3): swap for `sentence-transformers`
    (paraphrase-multilingual-MiniLM-L12-v2) once real semantic retrieval is needed. Add the
    dependency to brain/pyproject.toml when this is implemented, and update EMBEDDING_DIM to
    match the new model's output size (and the pgvector column it writes to).
    """

    async def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in digest[:EMBEDDING_DIM]]


class GeminiEmbeddingProvider(EmbeddingProvider):
    """TODO (docs/HANDOFF.md §1.3): implement against `google-genai`'s `gemini-embedding`
    model for real multilingual retrieval. Add the dependency and update EMBEDDING_DIM when
    this is implemented.
    """

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("GeminiEmbeddingProvider: see TODO above")


def create_embedding_provider() -> EmbeddingProvider:
    from ..config import settings

    match settings.embedding_provider:
        case "local":
            return LocalHashEmbeddingProvider()
        case "gemini":
            return GeminiEmbeddingProvider()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")
