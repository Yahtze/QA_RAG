from typing import Protocol
from uuid import UUID

from app.core.config import Settings


class EnqueueIngestionError(Exception):
    """Broker submit failed."""


class IngestionQueue(Protocol):
    async def enqueue_document_ingestion(self, document_id: UUID) -> None: ...


class CeleryIngestionQueue:
    def __init__(self, *, settings: Settings, celery_app=None):
        self.settings = settings
        if celery_app is None:
            from app.worker.celery_app import celery_app as default_celery_app

            celery_app = default_celery_app
        self.celery_app = celery_app

    async def enqueue_document_ingestion(self, document_id: UUID) -> None:
        try:
            self.celery_app.send_task(
                "documents.ingest", args=[str(document_id)], queue="ingestion"
            )
        except Exception as exc:
            raise EnqueueIngestionError("Failed to enqueue ingestion task.") from exc


class FakeIngestionQueue:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.enqueued: list[UUID] = []

    async def enqueue_document_ingestion(self, document_id: UUID) -> None:
        if self.fail:
            raise EnqueueIngestionError("Failed to enqueue ingestion task.")
        self.enqueued.append(document_id)
