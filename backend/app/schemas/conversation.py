from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    document_id: UUID | None = None
    active_document_ids: list[UUID] = Field(default_factory=list)


class ConversationOut(BaseModel):
    id: UUID
    document_id: UUID | None
    active_document_ids: list[UUID]
    dangling_user_message_id: UUID | None = None
    needs_retry: bool = False
    created_at: datetime


class ConversationScopeUpdate(BaseModel):
    active_document_ids: list[UUID]


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class CitationOut(BaseModel):
    id: UUID
    document_id: UUID
    chunk_id: UUID | None = None
    label: str | None = None
    filename: str | None = None
    chunk_text: str
    snippet: str | None = None
    page_number: int | None
    score: float
    fused_rank: int | None = None


class MessageOut(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    citations: list[CitationOut]


class MessagePairOut(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
