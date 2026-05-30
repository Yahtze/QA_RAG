from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.semantic_chunk_search import QdrantSemanticChunkSearch


class FakeEmbeddings:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3]]


class FakeQdrantClient:
    def __init__(self):
        self.called_with = None

    async def query_points(self, **kwargs):
        self.called_with = kwargs
        return SimpleNamespace(points=[SimpleNamespace(id=uuid4(), score=0.9)])


@pytest.mark.asyncio
async def test_semantic_search_uses_query_points(settings):
    service = QdrantSemanticChunkSearch(settings=settings, embeddings=FakeEmbeddings())
    fake_client = FakeQdrantClient()
    service.client = fake_client

    user_id = uuid4()
    doc_id = uuid4()
    hits = await service.search(user_id=user_id, document_ids=[doc_id], query="refund", top_k=5)

    assert len(hits) == 1
    assert hits[0].rank == 1
    assert fake_client.called_with is not None
    assert fake_client.called_with["query"] == [0.1, 0.2, 0.3]
    assert fake_client.called_with["limit"] == 5
