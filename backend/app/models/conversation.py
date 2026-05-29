from sqlalchemy import ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_user_created_id", "user_id", "created_at", "id"),)

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    active_document_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    user = relationship("User", back_populates="conversations")
    document = relationship("Document", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
