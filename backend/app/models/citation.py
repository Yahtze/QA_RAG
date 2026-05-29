from sqlalchemy import CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Citation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "citations"
    __table_args__ = (
        CheckConstraint("score >= 0.0 AND score <= 1.0", name="ck_citations_score_range"),
        Index("ix_citations_message_id", "message_id"),
    )

    message_id = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    document_id = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    score: Mapped[float] = mapped_column(default=0.0)

    message = relationship("Message", back_populates="citations")
