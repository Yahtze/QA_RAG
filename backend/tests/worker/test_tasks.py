import pytest

import app.worker.tasks
from app.models.user import User
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.ingestion_errors import DeterministicIngestionError, RetryableIngestionError


@pytest.mark.asyncio
async def test_worker_run_ingestion_calls_factory_and_commits(db_session, settings, monkeypatch):
    calls = []

    class Service:
        async def ingest_document(self, document_id):
            calls.append(document_id)

    monkeypatch.setattr("app.worker.tasks.build_ingestion_service", lambda **_: Service())
    await app.worker.tasks.run_ingestion("00000000-0000-0000-0000-000000000001", session=db_session, settings=settings)
    from uuid import UUID

    assert calls == [UUID("00000000-0000-0000-0000-000000000001")]


@pytest.mark.asyncio
async def test_final_retry_failure_marks_failed(db_session, settings):
    from app.worker.tasks import mark_final_retry_failure

    user = User(email="retry@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    repo = DocumentIngestionRepository(db_session)
    doc = await repo.create_pending(
        user=user,
        filename="doc.txt",
        content_type="text/plain",
        size_bytes=5,
        storage_path="uploads/doc.txt",
    )
    await repo.mark_processing(doc.id)

    await mark_final_retry_failure(db_session, doc.id, RuntimeError("boom"), max_retries=3)
    refreshed = await repo.get_document(doc.id)
    assert refreshed.status == "failed"
    assert refreshed.error_message == "Ingestion failed after 3 retries: boom"
