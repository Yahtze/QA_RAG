import pytest

from app.models.user import User
from app.services.embeddings import FakeEmbeddingProvider
from app.services.ingestion import TEXT_ZERO_CHUNKS_ERROR, IngestionService
from app.services.ingestion_errors import DeterministicIngestionError
from app.services.vector_store import VectorStore


class FakeStorage:
    def __init__(self, data: bytes):
        self.data = data

    async def store_upload(self, **kwargs):
        return type(
            "Stored",
            (),
            {
                "content_type": kwargs["content_type"],
                "size_bytes": len(self.data),
                "storage_path": "uploads/x.txt",
            },
        )()

    async def read_bytes(self, storage_path: str):
        return self.data


class RecordingVectorStore(VectorStore):
    def __init__(self):
        self.calls = []

    async def ensure_collection(self) -> None:
        self.calls.append("ensure_collection")

    async def delete_document_points(self, document_id) -> None:
        self.calls.append("delete_document_points")

    async def upsert_chunks(self, *, user_id, chunks, vectors) -> None:
        self.calls.append("upsert_chunks")


@pytest.mark.asyncio
async def test_zero_chunk_text_retained_as_failed(db_session, settings):
    user = User(email="ingest@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = IngestionService(
        session=db_session,
        settings=settings,
        storage=FakeStorage(data=b"   "),
        embedding_provider=FakeEmbeddingProvider(settings.EMBEDDING_DIMENSION),
        vector_store=RecordingVectorStore(),
    )

    class Upload:
        filename = "empty.txt"
        content_type = "text/plain"
        file = None

    out = await service.ingest_upload(user=user, upload_file=Upload())
    assert out.status.value == "failed"
    assert out.error_message == TEXT_ZERO_CHUNKS_ERROR
