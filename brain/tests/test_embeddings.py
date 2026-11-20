import pytest
from callmate_brain.memory.embeddings import EMBEDDING_DIM, LocalHashEmbeddingProvider


@pytest.mark.asyncio
async def test_local_embedding_has_exactly_embedding_dim_values():
    vector = await LocalHashEmbeddingProvider().embed("hello there")
    assert len(vector) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_local_embedding_is_deterministic():
    provider = LocalHashEmbeddingProvider()
    assert await provider.embed("same text") == await provider.embed("same text")


@pytest.mark.asyncio
async def test_local_embedding_differs_for_different_text():
    provider = LocalHashEmbeddingProvider()
    a = await provider.embed("caller asked about a delivery")
    b = await provider.embed("caller asked about an appointment")
    assert a != b


@pytest.mark.asyncio
async def test_local_embedding_values_are_in_unit_range():
    vector = await LocalHashEmbeddingProvider().embed("hello")
    assert all(0.0 <= value <= 1.0 for value in vector)
