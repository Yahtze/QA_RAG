from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.ingestion_types import IngestionPhase


class RecoveryClassification(StrEnum):
    QDRANT_NOT_SYNCED = "QDRANT_NOT_SYNCED"
    READY_NOT_MARKED = "READY_NOT_MARKED"
    PARTIAL_CHUNKS = "PARTIAL_CHUNKS"


class RecoveryAction(StrEnum):
    MARK_READY = "MARK_READY"
    QDRANT_UPSERT_ONLY = "QDRANT_UPSERT_ONLY"
    FULL_REINGEST = "FULL_REINGEST"
    MARK_FAILED = "MARK_FAILED"


@dataclass(frozen=True)
class StaleDocument:
    document_id: UUID
    status: str
    minutes_stale: int


@dataclass(frozen=True)
class RecoveryPlan:
    document_id: UUID
    classification: RecoveryClassification
    action: RecoveryAction
    reason: str


@dataclass(frozen=True)
class RecoveryResult:
    document_id: UUID
    action: RecoveryAction
    applied: bool


class IngestionReconciliationService:
    def __init__(self, *, session: AsyncSession, ingestion_service=None):
        self.session = session
        self.repo = DocumentIngestionRepository(session)
        self.ingestion_service = ingestion_service

    async def list_stale_processing(self, stale_after_minutes: int = 10) -> list[StaleDocument]:
        cutoff = datetime.now(UTC) - timedelta(minutes=stale_after_minutes)
        docs = (
            await self.session.execute(
                select(Document).where(
                    Document.status == DocumentStatus.PROCESSING.value,
                    Document.updated_at < cutoff,
                )
            )
        ).scalars().all()
        now = datetime.now(UTC)
        return [
            StaleDocument(
                document_id=doc.id,
                status=doc.status,
                minutes_stale=max(0, int((now - doc.updated_at).total_seconds() // 60)),
            )
            for doc in docs
        ]

    async def plan_recovery(self, document_id: UUID) -> RecoveryPlan:
        document = await self.repo.get_document(document_id)
        if document is None:
            raise ValueError("document not found")

        chunks = (
            await self.session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
        ).scalars().all()

        if document.qdrant_synced_at and document.status != DocumentStatus.READY.value:
            return RecoveryPlan(
                document_id=document_id,
                classification=RecoveryClassification.READY_NOT_MARKED,
                action=RecoveryAction.MARK_READY,
                reason="qdrant synced but document not ready",
            )

        if not chunks:
            return RecoveryPlan(
                document_id=document_id,
                classification=RecoveryClassification.PARTIAL_CHUNKS,
                action=RecoveryAction.FULL_REINGEST,
                reason="document has no persisted chunks",
            )

        if any(chunk.embedded_at is None for chunk in chunks):
            return RecoveryPlan(
                document_id=document_id,
                classification=RecoveryClassification.QDRANT_NOT_SYNCED,
                action=RecoveryAction.QDRANT_UPSERT_ONLY,
                reason="chunks exist but embedding sync incomplete",
            )

        return RecoveryPlan(
            document_id=document_id,
            classification=RecoveryClassification.PARTIAL_CHUNKS,
            action=RecoveryAction.FULL_REINGEST,
            reason="fallback reconciliation path",
        )

    async def apply_recovery(self, plan: RecoveryPlan) -> RecoveryResult:
        if plan.action == RecoveryAction.MARK_READY:
            chunks = await self.repo.get_chunks_for_vector_sync(plan.document_id)
            await self.repo.mark_ready_after_vector_sync(
                plan.document_id,
                page_count=max((chunk.page for chunk in chunks), default=0),
                chunk_count=len(chunks),
            )
            return RecoveryResult(document_id=plan.document_id, action=plan.action, applied=True)

        if plan.action == RecoveryAction.MARK_FAILED:
            await self.repo.mark_failed(
                plan.document_id,
                error_message="Marked failed during ingestion reconciliation.",
                phase=IngestionPhase.DATABASE,
            )
            return RecoveryResult(document_id=plan.document_id, action=plan.action, applied=True)

        if plan.action == RecoveryAction.FULL_REINGEST and self.ingestion_service is not None:
            await self.ingestion_service.ingest_document(plan.document_id)
            return RecoveryResult(document_id=plan.document_id, action=plan.action, applied=True)

        return RecoveryResult(document_id=plan.document_id, action=plan.action, applied=False)
