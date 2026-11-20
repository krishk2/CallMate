"""Embedding provider protocol. `reasoning`/`memory` code depends on `EmbeddingProvider`,
never on a concrete embedding model.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Literal

import structlog

logger = structlog.get_logger(__name__)

# Must match storage/models.py MemoryRow.embedding's Vector() dimension. 2048 matches NVIDIA
# NIM's nemotron-3-embed-1b output size (settings.nvidia_embedding_model) — change both
# together, with an Alembic migration, if you switch embedding models.
EMBEDDING_DIM = 2048

EmbeddingKind = Literal["query", "passage"]


class EmbeddingDimensionMismatch(Exception):
    def __init__(self, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"embedding provider returned {actual}-dim vector, but EMBEDDING_DIM={expected} "
            "(memory/embeddings.py) and the memories.embedding pgvector column are fixed at "
            "that size. Update EMBEDDING_DIM to match, then add an Alembic migration to "
            "resize the column, before using this provider."
        )


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str, *, kind: EmbeddingKind = "query") -> list[float]:
        """`kind` distinguishes a search query from a stored passage/document — asymmetric
        embedding models (e.g. NVIDIA NIM's) embed the two differently; symmetric ones can
        ignore it. Callers: memory/writer.py embeds what it stores as "passage"; everything
        retrieving/searching (persona/examples.py, reasoning via session_ws.py) uses the
        default "query".
        """


class LocalHashEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free stand-in: hashes text into a fixed-size vector with no
    semantic meaning. Enough to exercise the pgvector plumbing and pass tests. `kind` has no
    effect — this provider is symmetric (it isn't a real embedding model at all).
    """

    async def embed(self, text: str, *, kind: EmbeddingKind = "query") -> list[float]:
        # sha256 only yields 32 bytes; expand with a counter to reach EMBEDDING_DIM values
        # regardless of its size, rather than silently truncating/under-filling.
        values: list[float] = []
        counter = 0
        while len(values) < EMBEDDING_DIM:
            digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
            values.extend(byte / 255.0 for byte in digest)
            counter += 1
        return values[:EMBEDDING_DIM]


class NvidiaEmbeddingProvider(EmbeddingProvider):
    """NVIDIA NIM embeddings (e.g. `nvidia/nemotron-3-embed-1b`), OpenAI-compatible API plus
    the NIM-specific required `input_type` field (asymmetric models embed a search query
    differently from a stored passage) — passed via `extra_body`, since the OpenAI SDK's
    `embeddings.create` has no first-class parameter for it.

    Raises EmbeddingDimensionMismatch on the first real call rather than letting pgvector
    fail with a confusing error — resize the column (new Alembic migration) and update
    EMBEDDING_DIM before relying on a different model here.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        from openai import AsyncOpenAI

        from ..config import settings

        self._model = model or settings.nvidia_embedding_model
        self._client = AsyncOpenAI(
            api_key=api_key or settings.nvidia_api_key, base_url=settings.nvidia_base_url
        )

    async def embed(self, text: str, *, kind: EmbeddingKind = "query") -> list[float]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
            encoding_format="float",
            extra_body={"input_type": kind},
        )
        vector = response.data[0].embedding
        if len(vector) != EMBEDDING_DIM:
            raise EmbeddingDimensionMismatch(expected=EMBEDDING_DIM, actual=len(vector))
        return vector


def create_embedding_provider() -> EmbeddingProvider:
    from ..config import settings

    match settings.embedding_provider:
        case "local":
            return LocalHashEmbeddingProvider()
        case "nvidia":
            return NvidiaEmbeddingProvider()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")
