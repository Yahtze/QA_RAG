from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    document_id: UUID


class ConversationOut(BaseModel):
    id: UUID
    document_id: UUID
    created_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class CitationOut(BaseModel):
    id: UUID
    document_id: UUID
    chunk_text: str
    page_number: int | None
    score: float


class MessageOut(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    citations: list[CitationOut]


class MessagePairOut(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
