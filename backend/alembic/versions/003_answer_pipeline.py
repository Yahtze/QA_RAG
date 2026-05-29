"""answer pipeline

Revision ID: 003_answer_pipeline
Revises: 002_ingestion_pipeline
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_answer_pipeline"
down_revision: str | None = "002_ingestion_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_context().dialect.name

    # conversations.active_document_ids
    op.add_column("conversations", sa.Column("active_document_ids", sa.JSON(), nullable=True))
    op.execute("UPDATE conversations SET active_document_ids = json_array(document_id)")
    if dialect == "sqlite":
        with op.batch_alter_table("conversations") as batch_op:
            batch_op.alter_column("active_document_ids", nullable=False)
    else:
        op.alter_column("conversations", "active_document_ids", nullable=False)

    # messages columns
    op.add_column("messages", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("messages", sa.Column("original_query", sa.Text(), nullable=True))

    # citations columns
    op.add_column("citations", sa.Column("label", sa.String(length=20), nullable=True))
    op.add_column("citations", sa.Column("chunk_id", sa.Uuid(), nullable=True))
    op.add_column("citations", sa.Column("filename", sa.String(length=255), nullable=True))
    op.add_column("citations", sa.Column("snippet", sa.Text(), nullable=True))
    op.add_column("citations", sa.Column("lexical_rank", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("semantic_rank", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("fused_rank", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("fused_score", sa.Float(), nullable=True))
    op.create_index("ix_citations_chunk_id", "citations", ["chunk_id"])
    op.create_foreign_key("fk_citations_chunk_id", "citations", "document_chunks", ["chunk_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_citations_chunk_id", "citations", type_="foreignkey")
    op.drop_index("ix_citations_chunk_id", table_name="citations")
    for column in ["fused_score", "fused_rank", "semantic_rank", "lexical_rank", "snippet", "filename", "chunk_id", "label"]:
        op.drop_column("citations", column)
    for column in ["original_query", "retryable", "error_message"]:
        op.drop_column("messages", column)
    op.drop_column("conversations", "active_document_ids")
