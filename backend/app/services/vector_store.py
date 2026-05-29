"""Vector store module. This is the only module that knows Qdrant point/payload request shapes."""

from typing import Protocol
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.services.chunking import ChunkRecord
from app.services.ingestion_types import IngestionPhase
from app.services.qdrant_collection import QdrantCollectionService
from app.services.ingestion_errors import DeterministicIngestionError, IngestionError, RetryableIngestionError

DocumentChunkForVector = ChunkRecord


def build_payload(*, user_id: UUID, chunk: DocumentChunkForVector) -> dict:
    return {
        "user_id": str(user_id),
        "document_id": str(chunk.document_id),
        "source": chunk.source,
        "page": chunk.page,
        "chunk_index": chunk.chunk_index,
        "char_start": chunk.char_start,
        "char_end": chunk.char_end,
        "text": chunk.text,
        "text_hash": chunk.text_hash,
        "embedding_model": chunk.embedding_model,
    }


class VectorStore(Protocol):
    async def ensure_collection(self) -> None: ...

    async def delete_document_points(self, document_id: UUID) -> None: ...

    async def upsert_chunks(
        self, *, user_id: UUID, chunks: list[DocumentChunkForVector], vectors: list[list[float]]
    ) -> None: ...


def _classify_qdrant_error(exc: BaseException) -> IngestionError:
    if isinstance(exc, ResponseHandlingException):
        return RetryableIngestionError("vector_sync", exc)
    if isinstance(exc, UnexpectedResponse):
        if exc.status_code >= 500:
            return RetryableIngestionError("vector_sync", exc)
        return DeterministicIngestionError(str(exc), "vector_sync")
    return RetryableIngestionError("vector_sync", exc)


def _retryable_qdrant(exc: BaseException) -> bool:
    if isinstance(exc, UnexpectedResponse):
        return exc.status_code >= 500
    return isinstance(exc, ResponseHandlingException)


class QdrantVectorStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.collection_service = QdrantCollectionService(settings)
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    async def ensure_collection(self) -> None:
        try:
            await self.collection_service.ensure_collection()
        except (RetryableIngestionError, DeterministicIngestionError):
            raise
        except (ResponseHandlingException, UnexpectedResponse) as exc:
            raise _classify_qdrant_error(exc) from exc

    @retry(
        retry=retry_if_exception(_retryable_qdrant),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _delete_document_points_raw(self, document_id: UUID) -> None:
        flt = qm.Filter(
            must=[qm.FieldCondition(key="document_id", match=qm.MatchValue(value=str(document_id)))]
        )
        await self.client.delete(
            collection_name=self.settings.QDRANT_COLLECTION_NAME,
            points_selector=qm.FilterSelector(filter=flt),
        )

    async def delete_document_points(self, document_id: UUID) -> None:
        try:
            await self._delete_document_points_raw(document_id)
        except (RetryableIngestionError, DeterministicIngestionError):
            raise
        except (ResponseHandlingException, UnexpectedResponse) as exc:
            raise _classify_qdrant_error(exc) from exc

    @retry(
        retry=retry_if_exception(_retryable_qdrant),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _upsert_chunks_raw(
        self, *, user_id: UUID, chunks: list[DocumentChunkForVector], vectors: list[list[float]]
    ) -> None:
        points = [
            qm.PointStruct(
                id=str(chunk.id), vector=vector, payload=build_payload(user_id=user_id, chunk=chunk)
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            await self.client.upsert(
                collection_name=self.settings.QDRANT_COLLECTION_NAME, points=points
            )

    async def upsert_chunks(
        self, *, user_id: UUID, chunks: list[DocumentChunkForVector], vectors: list[list[float]]
    ) -> None:
        try:
            await self._upsert_chunks_raw(user_id=user_id, chunks=chunks, vectors=vectors)
        except (RetryableIngestionError, DeterministicIngestionError):
            raise
        except (ResponseHandlingException, UnexpectedResponse) as exc:
            raise _classify_qdrant_error(exc) from exc
