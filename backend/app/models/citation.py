import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Citation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "citations"
    __table_args__ = (
        CheckConstraint(
            "score >= 0.0 AND score <= 1.0", name="ck_citations_score_range"
        ),
        Index("ix_citations_message_id", "message_id"),
    )

    message_id = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    document_id = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    score: Mapped[float] = mapped_column(default=0.0)
    label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    lexical_rank: Mapped[int | None] = mapped_column(nullable=True)
    semantic_rank: Mapped[int | None] = mapped_column(nullable=True)
    fused_rank: Mapped[int | None] = mapped_column(nullable=True)
    fused_score: Mapped[float | None] = mapped_column(nullable=True)

    message = relationship("Message", back_populates="citations")
