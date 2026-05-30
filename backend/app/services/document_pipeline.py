import logging

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import (
    build_cursor_predicate,
    decode_cursor,
    normalize_limit,
    page_from_items,
)
from app.models import Document, User
from app.schemas.document import DeletedDocumentOut, DocumentOut

logger = logging.getLogger(__name__)


class NotFoundError(Exception): ...


class ForbiddenError(Exception): ...


class DocumentPipelineService:
    def __init__(
        self, session: AsyncSession, storage, ingestion_service=None, vector_store=None
    ):
        self.session = session
        self.storage = storage
        self.ingestion_service = ingestion_service
        self.vector_store = vector_store

    async def upload(self, *, user: User, upload_file: UploadFile) -> DocumentOut:
        if self.ingestion_service is None:
            raise RuntimeError("ingestion_service is required for upload")
        return await self.ingestion_service.ingest_upload(
            user=user, upload_file=upload_file
        )

    async def list(self, *, user: User, cursor: str | None, limit: int | None):
        lim = normalize_limit(limit)
        cur = decode_cursor(cursor)
        q = select(Document).where(Document.user_id == user.id)
        pred = build_cursor_predicate(Document.created_at, Document.id, cur)
        if pred is not None:
            q = q.where(pred)
        q = q.order_by(Document.created_at, Document.id).limit(lim + 1)
        items = list((await self.session.execute(q)).scalars().all())
        out = [DocumentOut.model_validate(x, from_attributes=True) for x in items]
        return page_from_items(
            out,
            lim,
            lambda d: type("C", (), {"created_at": d.created_at, "id": d.id})(),
        )

    async def get(self, *, user: User, document_id):
        doc = (
            await self.session.execute(
                select(Document).where(Document.id == document_id)
            )
        ).scalar_one_or_none()
        if not doc:
            raise NotFoundError
        if doc.user_id != user.id:
            raise ForbiddenError
        return DocumentOut.model_validate(doc, from_attributes=True)

    async def delete(self, *, user: User, document_id):
        doc = (
            await self.session.execute(
                select(Document).where(Document.id == document_id)
            )
        ).scalar_one_or_none()
        if not doc:
            raise NotFoundError
        if doc.user_id != user.id:
            raise ForbiddenError
        if self.vector_store is not None:
            await self.vector_store.delete_document_points(document_id)
        path = doc.storage_path
        await self.session.delete(doc)
        await self.session.commit()
        try:
            await self.storage.delete(path)
        except Exception:
            logger.warning(
                "document_file_delete_failed",
                extra={"document_id": str(document_id), "storage_path": path},
            )
        return DeletedDocumentOut(id=document_id)
