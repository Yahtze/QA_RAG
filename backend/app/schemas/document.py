from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    page_count: int | None = None
    chunk_count: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentAdminOut(DocumentOut):
    qdrant_synced_at: datetime | None = None
    retention_note: str | None = None
    retry_count: int = 0
    last_retry_at: datetime | None = None


class DeletedDocumentOut(BaseModel):
    id: UUID
    deleted: bool = True


class BatchUploadItemOut(BaseModel):
    filename: str
    status: str
    document: DocumentOut | None = None
    error: str | None = None


class BatchUploadSummaryOut(BaseModel):
    total: int
    accepted: int
    failed: int
    results: list[BatchUploadItemOut]
