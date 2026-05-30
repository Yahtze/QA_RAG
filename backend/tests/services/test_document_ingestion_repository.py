import pytest
from sqlalchemy import select
from uuid import UUID

from app.models.document import DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.chunking import ChunkRecord
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.ingestion_types import IngestionPhase


@pytest.mark.asyncio
async def test_replace_chunks_and_mark_ready(db_session):
    user = User(email="repo@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repo = DocumentIngestionRepository(db_session)
    doc = await repo.create_pending(
        user=user,
        filename="a.txt",
        content_type="text/plain",
        size_bytes=3,
        storage_path="stored/a.txt",
    )
    await repo.mark_processing(doc.id)
    chunk = ChunkRecord(
        UUID("22222222-2222-2222-2222-222222222222"),
        doc.id,
        "a.txt",
        1,
        0,
        0,
        3,
        "abc",
        "hashhashhashhash",
        "model",
    )
    await repo.replace_chunks_pending_embedding(doc.id, [chunk])
    chunks = await repo.get_chunks_for_vector_sync(doc.id)
    assert len(chunks) == 1
    await repo.mark_ready_after_vector_sync(doc.id, page_count=1, chunk_count=1)
    await db_session.refresh(doc)
    assert doc.status == DocumentStatus.READY.value
    assert doc.chunk_count == 1
    assert doc.qdrant_synced_at is not None
    db_chunks = (
        (
            await db_session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            )
        )
        .scalars()
        .all()
    )
    assert all(c.embedded_at is not None for c in db_chunks)
    assert all(c.embedded_at.tzinfo is None for c in db_chunks)


@pytest.mark.asyncio
async def test_create_pending_without_commit_is_in_transaction(db_session):
    repo = DocumentIngestionRepository(db_session)
    user = User(email="pending@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    doc = await repo.create_pending_without_commit(
        user=user,
        filename="doc.txt",
        content_type="text/plain",
        size_bytes=5,
        storage_path="uploads/doc.txt",
    )
    assert doc.status == DocumentStatus.PENDING.value
    assert doc.id is not None


@pytest.mark.asyncio
async def test_mark_failed_message_for_enqueue_failure(db_session):
    repo = DocumentIngestionRepository(db_session)
    user = User(email="failed@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    doc = await repo.create_pending(
        user=user,
        filename="doc.txt",
        content_type="text/plain",
        size_bytes=5,
        storage_path="uploads/doc.txt",
    )

    await repo.mark_failed(
        doc.id,
        error_message="Failed to enqueue ingestion task.",
        phase=IngestionPhase.DATABASE,
    )
    refreshed = await repo.get_document(doc.id)
    assert refreshed.status == DocumentStatus.FAILED.value
    assert refreshed.error_message == "Failed to enqueue ingestion task."
