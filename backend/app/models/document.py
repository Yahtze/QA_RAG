from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','processing','ready','failed')", name="ck_documents_status"
        ),
        Index("ix_documents_user_created_id", "user_id", "created_at", "id"),
    )

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int]
    storage_path: Mapped[str] = mapped_column(String(512), unique=True)
    status: Mapped[str] = mapped_column(String(20), default=DocumentStatus.PENDING.value)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(nullable=True)
    qdrant_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retention_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="documents")
    conversations = relationship(
        "Conversation", back_populates="document", cascade="all, delete-orphan"
    )
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
