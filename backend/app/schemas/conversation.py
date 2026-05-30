import re
import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

MAX_USER_QUERY_CHARS = 4000


def normalize_user_query(content: str) -> str:
    trimmed = content.strip()
    collapsed = re.sub(r"\s+", " ", trimmed)
    without_controls = "".join(
        ch
        for ch in collapsed
        if ch in {"\n", "\t"} or not unicodedata.category(ch).startswith("C")
    )
    collapsed_clean = re.sub(r"\s+", " ", without_controls).strip()
    return unicodedata.normalize("NFC", collapsed_clean)


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
    content: str

    @field_validator("content", mode="before")
    @classmethod
    def validate_and_normalize_content(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("content must be a string")
        normalized = normalize_user_query(value)
        if not normalized:
            raise ValueError("content cannot be empty after normalization")
        if len(normalized) > MAX_USER_QUERY_CHARS:
            raise ValueError(
                f"content exceeds max length of {MAX_USER_QUERY_CHARS} characters"
            )
        return normalized


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
