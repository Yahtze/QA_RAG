"""ingestion pipeline

Revision ID: 002_ingestion_pipeline
Revises: 001_initial_schema
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_ingestion_pipeline"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE documents SET status = 'pending' WHERE status = 'uploading'")
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status", "documents", "status IN ('pending','processing','ready','failed')"
    )
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("chunk_count", sa.Integer(), nullable=True))
    op.add_column(
        "documents", sa.Column("qdrant_synced_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("documents", sa.Column("retention_note", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "documents", sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=16), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "page",
            "chunk_index",
            "char_start",
            "char_end",
            name="uq_document_chunks_position",
        ),
    )
    op.create_index(
        "ix_document_chunks_document_page_chunk",
        "document_chunks",
        ["document_id", "page", "chunk_index"],
    )
    op.create_index(
        "ix_document_chunks_document_embedded", "document_chunks", ["document_id", "embedded_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_embedded", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_page_chunk", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_column("documents", "last_retry_at")
    op.drop_column("documents", "retry_count")
    op.drop_column("documents", "retention_note")
    op.drop_column("documents", "qdrant_synced_at")
    op.drop_column("documents", "chunk_count")
    op.drop_column("documents", "page_count")
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status", "documents", "status IN ('uploading','processing','ready','failed')"
    )
    op.execute("UPDATE documents SET status = 'uploading' WHERE status = 'pending'")
