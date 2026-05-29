from sqlalchemy import inspect

from app.db.base import Base
from app.models.document import DocumentStatus
from app.models.document_chunk import DocumentChunk


def test_document_status_values_are_ingestion_states():
    assert [s.value for s in DocumentStatus] == ["pending", "processing", "ready", "failed"]


def test_document_ingestion_columns_exist():
    columns = {c.name for c in Base.metadata.tables["documents"].columns}
    assert {
        "page_count",
        "chunk_count",
        "qdrant_synced_at",
        "retention_note",
        "retry_count",
        "last_retry_at",
    } <= columns


def test_document_chunks_table_shape():
    table = Base.metadata.tables["document_chunks"]
    columns = {c.name for c in table.columns}
    assert {
        "id",
        "document_id",
        "source",
        "page",
        "chunk_index",
        "char_start",
        "char_end",
        "text",
        "text_hash",
        "embedding_model",
        "embedded_at",
        "created_at",
    } <= columns
    assert inspect(DocumentChunk).relationships["document"].back_populates == "chunks"


def test_answer_pipeline_columns_exist():
    from app.models import Citation, Conversation, Message

    assert "active_document_ids" in Conversation.__table__.columns
    assert "error_message" in Message.__table__.columns
    assert "retryable" in Message.__table__.columns
    assert "original_query" in Message.__table__.columns
    assert "label" in Citation.__table__.columns
    assert "chunk_id" in Citation.__table__.columns
    assert "filename" in Citation.__table__.columns
    assert "snippet" in Citation.__table__.columns
    assert "fused_rank" in Citation.__table__.columns
