import pytest

from app.services.semantic_cache import RedisSemanticCache


class FakeEmbeddings:
    async def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3]]


class FakeRedisClient:
    def __init__(self):
        self.calls = []

    async def execute_command(self, *args):
        self.calls.append(args)
        return [
            1,
            b"semcache:key",
            [
                b"distance",
                b"0.01",
                b"response",
                b"cached answer",
                b"chunk_ids",
                b'["chunk-1", "chunk-2"]',
            ],
        ]


@pytest.mark.asyncio
async def test_semantic_cache_get_returns_chunk_ids(settings):
    cache = RedisSemanticCache(settings, FakeEmbeddings())
    cache.client = FakeRedisClient()

    async def _skip_index():
        return None

    cache._ensure_index = _skip_index

    hit = await cache.get(query="Refunds?", document_ids=["doc-1"])

    assert hit is not None
    assert hit.answer == "cached answer"
    assert hit.chunk_ids == ["chunk-1", "chunk-2"]

    search_call = cache.client.calls[0]
    assert "RETURN" in search_call
    return_idx = search_call.index("RETURN")
    assert search_call[return_idx + 2 : return_idx + 5] == (
        "distance",
        "response",
        "chunk_ids",
    )
