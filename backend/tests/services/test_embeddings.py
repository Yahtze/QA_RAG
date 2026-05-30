import pytest

from app.services.embeddings import (
    EmbeddingValidationError,
    FakeEmbeddingProvider,
    validate_embeddings,
)


@pytest.mark.asyncio
async def test_fake_embedder_is_deterministic_and_dimensioned():
    provider = FakeEmbeddingProvider(dimension=4)
    assert await provider.embed_texts(["abc"]) == await provider.embed_texts(["abc"])
    assert len((await provider.embed_texts(["abc"]))[0]) == 4


def test_validate_embeddings_count_mismatch():
    with pytest.raises(
        EmbeddingValidationError, match="returned 1 vectors for 2 texts"
    ):
        validate_embeddings(texts=["a", "b"], vectors=[[0.1]], dimension=1)


def test_validate_embeddings_dimension_mismatch():
    with pytest.raises(
        EmbeddingValidationError, match="vector 0 has dimension 2; expected 3"
    ):
        validate_embeddings(texts=["a"], vectors=[[0.1, 0.2]], dimension=3)
