"""Repository module. This is the only module that knows ingestion SQL transaction details."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.chunking import ChunkRecord
from app.services.ingestion_types import IngestionPhase


class DocumentIngestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_pending_without_commit(
        self, *, user: User, filename: str, content_type: str, size_bytes: int, storage_path: str
    ) -> Document:
        doc = Document(
            user_id=user.id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            status=DocumentStatus.PENDING.value,
        )
        self.session.add(doc)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def commit(self) -> None:
        await self.session.commit()

    async def create_pending(
        self, *, user: User, filename: str, content_type: str, size_bytes: int, storage_path: str
    ) -> Document:
        doc = await self.create_pending_without_commit(
            user=user,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        await self.commit()
        await self.session.refresh(doc)
        return doc

    async def get_document(self, document_id: UUID) -> Document | None:
        return (
            await self.session.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()

    async def mark_processing(self, document_id: UUID) -> None:
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status=DocumentStatus.PROCESSING.value, error_message=None)
        )
        await self.session.commit()

    async def replace_chunks_pending_embedding(
        self, document_id: UUID, chunks: list[ChunkRecord]
    ) -> None:
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        self.session.add_all([DocumentChunk(**chunk.__dict__) for chunk in chunks])
        await self.session.commit()

    async def mark_ready_after_vector_sync(
        self, document_id: UUID, *, page_count: int, chunk_count: int
    ) -> None:
        aware_now = datetime.now(UTC)
        naive_utc_now = aware_now.replace(tzinfo=None)
        await self.session.execute(
            update(DocumentChunk)
            .where(DocumentChunk.document_id == document_id, DocumentChunk.embedded_at.is_(None))
            .values(embedded_at=naive_utc_now)
        )
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=DocumentStatus.READY.value,
                error_message=None,
                qdrant_synced_at=aware_now,
                page_count=page_count,
                chunk_count=chunk_count,
            )
        )
        await self.session.commit()

    async def mark_failed(
        self, document_id: UUID, *, error_message: str, phase: IngestionPhase
    ) -> None:
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=DocumentStatus.FAILED.value,
                error_message=error_message,
                retention_note=f"failed during {phase.value}",
            )
        )
        await self.session.commit()

    async def get_chunks_for_vector_sync(self, document_id: UUID) -> list[ChunkRecord]:
        rows = (
            (
                await self.session.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.document_id == document_id)
                    .order_by(DocumentChunk.page, DocumentChunk.chunk_index)
                )
            )
            .scalars()
            .all()
        )
        return [
            ChunkRecord(
                id=r.id,
                document_id=r.document_id,
                source=r.source,
                page=r.page,
                chunk_index=r.chunk_index,
                char_start=r.char_start,
                char_end=r.char_end,
                text=r.text,
                text_hash=r.text_hash,
                embedding_model=r.embedding_model,
            )
            for r in rows
        ]
