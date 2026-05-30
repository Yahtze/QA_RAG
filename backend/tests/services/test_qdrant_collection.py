from types import SimpleNamespace

import pytest

from app.services.qdrant_collection import (
    QdrantCollectionMismatchError,
    QdrantCollectionService,
)


@pytest.mark.asyncio
async def test_qdrant_ensure_create(monkeypatch, settings):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.created = False

        async def get_collections(self):
            return SimpleNamespace(collections=[])

        async def create_collection(self, **kwargs):
            self.created = True

        async def create_payload_index(self, **kwargs):
            return None

        async def close(self):
            return None

    fake = FakeClient()
    monkeypatch.setattr(
        "app.services.qdrant_collection.AsyncQdrantClient", lambda **_: fake
    )
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
                    params=SimpleNamespace(
                        vectors=SimpleNamespace(size=10, distance="Cosine")
                    )
                )
            )

        async def create_payload_index(self, **kwargs):
            return None

        async def close(self):
            return None

    monkeypatch.setattr(
        "app.services.qdrant_collection.AsyncQdrantClient", lambda **_: FakeClient()
    )
    with pytest.raises(QdrantCollectionMismatchError):
        await QdrantCollectionService(settings).ensure_collection()


@pytest.mark.asyncio
async def test_collection_service_creates_payload_indexes(monkeypatch, settings):
    calls = []

    class Client:
        async def get_collections(self):
            return type("Collections", (), {"collections": []})()

        async def create_collection(self, **kwargs):
            calls.append(("create_collection", kwargs))

        async def create_payload_index(self, **kwargs):
            calls.append(("create_payload_index", kwargs))

        async def close(self):
            pass

    monkeypatch.setattr(
        "app.services.qdrant_collection.AsyncQdrantClient", lambda **_: Client()
    )
    await QdrantCollectionService(settings).ensure_collection()
    assert (
        "create_payload_index",
        {
            "collection_name": settings.QDRANT_COLLECTION_NAME,
            "field_name": "document_id",
            "field_schema": "keyword",
        },
    ) in calls
    assert (
        "create_payload_index",
        {
            "collection_name": settings.QDRANT_COLLECTION_NAME,
            "field_name": "user_id",
            "field_schema": "keyword",
        },
    ) in calls
