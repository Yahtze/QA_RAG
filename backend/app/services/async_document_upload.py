import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.ingestion_queue import EnqueueIngestionError, IngestionQueue
from app.services.ingestion_types import IngestionPhase
from app.services.storage import LocalStorageService

logger = logging.getLogger(__name__)
ENQUEUE_FAILURE_MESSAGE = "Failed to enqueue ingestion task."


class AsyncDocumentUpload:
    def __init__(self, *, session: AsyncSession, settings: Settings, queue: IngestionQueue):
        self.session = session
        self.settings = settings
        self.queue = queue
        self.storage = LocalStorageService(settings)
        self.repo = DocumentIngestionRepository(session)

    async def upload(self, *, user: User, upload_file: UploadFile) -> DocumentOut:
        document_id = uuid.uuid4()
        stored = await self.storage.store_upload(
            user_id=user.id,
            document_id=document_id,
            filename=upload_file.filename or "upload.bin",
            content_type=upload_file.content_type or "application/octet-stream",
            upload=upload_file.file,
        )
        document = await self.repo.create_pending_without_commit(
            user=user,
            filename=upload_file.filename or "upload.bin",
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            storage_path=stored.storage_path,
        )
        await self.repo.commit()
        try:
            logger.info("api_ingestion_enqueue_requested", extra={"document_id": str(document.id)})
            await self.queue.enqueue_document_ingestion(document.id)
            logger.info("api_ingestion_enqueue_succeeded", extra={"document_id": str(document.id)})
        except EnqueueIngestionError:
            logger.exception(
                "api_ingestion_enqueue_failed", extra={"document_id": str(document.id)}
            )
            try:
                await self.repo.mark_failed(
                    document.id,
                    error_message=ENQUEUE_FAILURE_MESSAGE,
                    phase=IngestionPhase.DATABASE,
                )
            except Exception:
                logger.exception(
                    "api_ingestion_enqueue_failed_status_update_failed",
                    extra={"document_id": str(document.id)},
                )
            raise
        await self.session.refresh(document)
        return DocumentOut.model_validate(document, from_attributes=True)
