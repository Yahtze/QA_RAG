from uuid import uuid4

import pytest

from app.services.ingestion_queue import (
    CeleryIngestionQueue,
    EnqueueIngestionError,
    FakeIngestionQueue,
)


@pytest.mark.asyncio
async def test_fake_queue_records_document_id_without_task_id():
    q = FakeIngestionQueue()
    document_id = uuid4()

    result = await q.enqueue_document_ingestion(document_id)

    assert result is None
    assert q.enqueued == [document_id]


@pytest.mark.asyncio
async def test_fake_queue_can_fail():
    q = FakeIngestionQueue(fail=True)
    with pytest.raises(EnqueueIngestionError):
        await q.enqueue_document_ingestion(uuid4())


@pytest.mark.asyncio
async def test_celery_queue_uses_send_task_and_hides_task_id(settings):
    calls = []

    class App:
        def send_task(self, name, args, queue):
            calls.append((name, args, queue))
            return object()

    document_id = uuid4()
    result = await CeleryIngestionQueue(
        settings=settings, celery_app=App()
    ).enqueue_document_ingestion(document_id)

    assert result is None
    assert calls == [("documents.ingest", [str(document_id)], "ingestion")]
