from types import SimpleNamespace

import pytest

from app.services.qdrant_collection import QdrantCollectionMismatchError, QdrantCollectionService


@pytest.mark.asyncio
async def test_qdrant_ensure_create(monkeypatch, settings):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.created = False

        async def get_collections(self):
            return SimpleNamespace(collections=[])

        async def create_collection(self, **kwargs):
            self.created = True

        async def close(self):
            return None

    fake = FakeClient()
    monkeypatch.setattr("app.services.qdrant_collection.AsyncQdrantClient", lambda **_: fake)
    await QdrantCollectionService(settings).ensure_collection()
    assert fake.created is True


@pytest.mark.asyncio
async def test_qdrant_dimension_mismatch(monkeypatch, settings):
    class FakeClient:
        async def get_collections(self):
            return SimpleNamespace(
                collections=[SimpleNamespace(name=settings.QDRANT_COLLECTION_NAME)]
            )

        async def get_collection(self, _name):
            return SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(vectors=SimpleNamespace(size=10))
                )
            )

        async def close(self):
            return None

    monkeypatch.setattr(
        "app.services.qdrant_collection.AsyncQdrantClient", lambda **_: FakeClient()
    )
    with pytest.raises(QdrantCollectionMismatchError):
        await QdrantCollectionService(settings).ensure_collection()
