import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import (
    build_cursor_predicate,
    decode_cursor,
    normalize_limit,
    page_from_items,
)
from app.models import Document, DocumentStatus, User
from app.schemas.document import DocumentOut
from app.services.storage import LocalStorageService


class NotFoundError(Exception): ...


class ForbiddenError(Exception): ...


class DocumentPipelineService:
    def __init__(self, session: AsyncSession, storage: LocalStorageService):
        self.session = session
        self.storage = storage

    async def upload(self, *, user: User, upload_file: UploadFile) -> DocumentOut:
        doc_id = uuid.uuid4()
        stored = await self.storage.store_upload(
            user_id=user.id,
            document_id=doc_id,
            filename=upload_file.filename or "upload.bin",
            content_type=upload_file.content_type or "application/octet-stream",
            upload=upload_file.file,
        )
        doc = Document(
            id=doc_id,
            user_id=user.id,
            filename=upload_file.filename or "upload.bin",
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            storage_path=stored.storage_path,
            status=DocumentStatus.READY.value,
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return DocumentOut.model_validate(doc, from_attributes=True)

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
            out, lim, lambda d: type("C", (), {"created_at": d.created_at, "id": d.id})()
        )

    async def get(self, *, user: User, document_id):
        doc = (
            await self.session.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()
        if not doc:
            raise NotFoundError
        if doc.user_id != user.id:
            raise ForbiddenError
        return DocumentOut.model_validate(doc, from_attributes=True)

    async def delete(self, *, user: User, document_id):
        doc = (
            await self.session.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()
        if not doc:
            raise NotFoundError
        if doc.user_id != user.id:
            raise ForbiddenError
        path = doc.storage_path
        await self.session.delete(doc)
        await self.session.commit()
        await self.storage.delete(path)
