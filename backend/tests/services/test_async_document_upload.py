import pytest

from app.models.user import User
from app.services.async_document_upload import AsyncDocumentUpload
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.ingestion_queue import EnqueueIngestionError, FakeIngestionQueue


class Upload:
    filename = "doc.txt"
    content_type = "text/plain"

    def __init__(self, data=b"hello"):
        from io import BytesIO

        self.file = BytesIO(data)


@pytest.mark.asyncio
async def test_async_upload_stores_pending_commits_then_enqueues(db_session, settings):
    user = User(email="async@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    queue = FakeIngestionQueue()

    out = await AsyncDocumentUpload(
        session=db_session,
        settings=settings,
        queue=queue,
    ).upload(user=user, upload_file=Upload())

    assert out.status.value == "pending"
    assert queue.enqueued == [out.id]
    doc = await DocumentIngestionRepository(db_session).get_document(out.id)
    assert doc is not None
    assert doc.status == "pending"


@pytest.mark.asyncio
async def test_enqueue_failure_marks_failed_and_raises(db_session, settings):
    user = User(email="fail-enqueue@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    with pytest.raises(EnqueueIngestionError):
        await AsyncDocumentUpload(
            session=db_session,
            settings=settings,
            queue=FakeIngestionQueue(fail=True),
        ).upload(user=user, upload_file=Upload())
