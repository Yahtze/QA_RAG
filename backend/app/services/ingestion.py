"""Ingestion orchestration module. Must not import PyMuPDF or Qdrant HTTP models directly."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services.chunking import chunk_pages
from app.services.document_extraction import ExtractionError, extract_document
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.embeddings import EmbeddingProvider
from app.services.ingestion_types import IngestionPhase
from app.services.storage import LocalStorageService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

PDF_ZERO_CHUNKS_ERROR = "No extractable text found — likely a scanned or image-only PDF."
TEXT_ZERO_CHUNKS_ERROR = "No extractable text found in document."
GENERIC_INGESTION_ERROR = (
    "An unexpected error occurred during ingestion. The document has been retained for review."
)


class NonRetryableIngestionError(Exception):
    def __init__(self, message: str, phase: IngestionPhase):
        super().__init__(message)
        self.message = message
        self.phase = phase


class RetryableIngestionError(Exception):
    def __init__(self, phase: IngestionPhase, cause: BaseException):
        super().__init__(str(cause))
        self.phase = phase
        self.cause = cause


class IngestionService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        storage: LocalStorageService,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ):
        self.settings = settings
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.repo = DocumentIngestionRepository(session)

    async def ingest_upload(self, *, user: User, upload_file):
        stored = await self.storage.store_upload(
            user_id=user.id,
            document_id=uuid.uuid4(),
            filename=upload_file.filename or "upload.bin",
            content_type=upload_file.content_type or "application/octet-stream",
            upload=upload_file.file,
        )
        document = await self.repo.create_pending(
            user=user,
            filename=upload_file.filename or "upload.bin",
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            storage_path=stored.storage_path,
        )
        return await self.ingest_document(document.id)

    async def ingest_document(self, document_id):
        phase = IngestionPhase.DATABASE
        try:
            document = await self.repo.get_document(document_id)
            if document is None:
                raise NonRetryableIngestionError("Document not found", IngestionPhase.DATABASE)
            await self.repo.mark_processing(document_id)

            phase = IngestionPhase.STORAGE_READ
            data = await self.storage.read_bytes(document.storage_path)

            phase = IngestionPhase.EXTRACTION
            extracted = await extract_document(
                filename=document.filename, content_type=document.content_type, data=data
            )

            phase = IngestionPhase.CHUNKING
            chunks = chunk_pages(
                document_id=document.id,
                source=document.filename,
                pages=extracted.pages,
                chunk_size=self.settings.CHUNK_SIZE_CHARS,
                chunk_overlap=self.settings.CHUNK_OVERLAP_CHARS,
                embedding_model=self.settings.EMBEDDING_MODEL,
            )
            if not chunks:
                if document.content_type == "application/pdf":
                    logger.warning(
                        "document_zero_chunks",
                        extra={
                            "document_id": str(document_id),
                            "reason": "no_extractable_text",
                            "page_count": extracted.page_count,
                        },
                    )
                    raise NonRetryableIngestionError(PDF_ZERO_CHUNKS_ERROR, phase)
                raise NonRetryableIngestionError(TEXT_ZERO_CHUNKS_ERROR, phase)

            phase = IngestionPhase.EMBEDDING
            vectors = await self.embedding_provider.embed_texts([c.text for c in chunks])

            phase = IngestionPhase.DATABASE
            await self.repo.replace_chunks_pending_embedding(document.id, chunks)

            phase = IngestionPhase.VECTOR_SYNC
            await self.vector_store.ensure_collection()
            await self.vector_store.delete_document_points(document.id)
            await self.vector_store.upsert_chunks(
                user_id=document.user_id, chunks=chunks, vectors=vectors
            )

            phase = IngestionPhase.DATABASE
            await self.repo.mark_ready_after_vector_sync(
                document.id, page_count=extracted.page_count, chunk_count=len(chunks)
            )
            document = await self.repo.get_document(document.id)
            return DocumentOut.model_validate(document)
        except (ExtractionError, NonRetryableIngestionError) as exc:
            msg = exc.message if isinstance(exc, NonRetryableIngestionError) else exc.message
            fail_phase = (
                exc.phase
                if isinstance(exc, NonRetryableIngestionError)
                else IngestionPhase.EXTRACTION
            )
            await self.repo.mark_failed(document_id, error_message=msg, phase=fail_phase)
            document = await self.repo.get_document(document_id)
            return DocumentOut.model_validate(document)
        except Exception:
            logger.exception(
                "document_ingestion_failed",
                extra={"document_id": str(document_id), "phase": phase.value},
            )
            await self.repo.mark_failed(
                document_id, error_message=GENERIC_INGESTION_ERROR, phase=phase
            )
            document = await self.repo.get_document(document_id)
            return DocumentOut.model_validate(document)
