from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: Literal["uploading", "processing", "ready", "failed"]
    error_message: str | None
    created_at: datetime
    updated_at: datetime
