from uuid import uuid4

import pytest

from app.models import Conversation, Document, DocumentChunk, DocumentStatus, User
from app.services.conversation_scope import ConversationScopeService
from app.services.hybrid_retrieval import HybridRetriever, RankedChunkHit, reciprocal_rank_fusion


class FakeLexical:
    def __init__(self, hits):
        self.hits = hits

    async def search(self, **kwargs):
        return self.hits


class FakeSemantic:
    def __init__(self, hits):
        self.hits = hits

    async def search(self, **kwargs):
        return self.hits


async def make_fixture(db_session):
    user = User(email="r@example.com", hashed_password="x", name="R")
    other = User(email="o@example.com", hashed_password="x", name="O")
    db_session.add_all([user, other])
    await db_session.commit()
    ready = Document(
        user_id=user.id,
        filename="ready.pdf",
        content_type="application/pdf",
        size_bytes=1,
        storage_path="ready",
        status=DocumentStatus.READY.value,
    )
    inactive = Document(
        user_id=user.id,
        filename="inactive.pdf",
        content_type="application/pdf",
        size_bytes=1,
        storage_path="inactive",
        status=DocumentStatus.READY.value,
    )
    failed = Document(
        user_id=user.id,
        filename="failed.pdf",
        content_type="application/pdf",
        size_bytes=1,
        storage_path="failed",
        status=DocumentStatus.FAILED.value,
    )
    wrong = Document(
        user_id=other.id,
        filename="wrong.pdf",
        content_type="application/pdf",
        size_bytes=1,
        storage_path="wrong",
        status=DocumentStatus.READY.value,
    )
    db_session.add_all([ready, inactive, failed, wrong])
    await db_session.commit()

    chunks = []
    for doc, text in [
        (ready, "refund policy"),
        (inactive, "inactive policy"),
        (failed, "failed policy"),
        (wrong, "wrong policy"),
    ]:
        c = DocumentChunk(
            id=uuid4(),
            document_id=doc.id,
            source=doc.filename,
            page=1,
            chunk_index=0,
            char_start=0,
            char_end=len(text),
            text=text,
            text_hash="h",
            embedding_model="m",
        )
        chunks.append(c)
    db_session.add_all(chunks)
    conv = Conversation(user_id=user.id, document_id=ready.id, active_document_ids=[str(ready.id)])
    db_session.add(conv)
    await db_session.commit()
    return user, conv, chunks


def test_rrf_merge_dedupe_prefers_dual_hits():
    a, b, c = uuid4(), uuid4(), uuid4()
    fused = reciprocal_rank_fusion(
        lexical=[RankedChunkHit(a, 1, 0.9), RankedChunkHit(b, 2, 0.8)],
        semantic=[RankedChunkHit(c, 1, 0.7), RankedChunkHit(a, 2, 0.6)],
        final_top_k=3,
    )
    assert [x.chunk_id for x in fused] == [a, c, b]
    assert fused[0].lexical_rank == 1
    assert fused[0].semantic_rank == 2


@pytest.mark.asyncio
async def test_hybrid_retrieval_filters_to_active_ready_user_chunks(db_session, settings):
    user, conv, chunks = await make_fixture(db_session)
    active_chunk, inactive_chunk, failed_chunk, wrong_chunk = chunks
    lexical = FakeLexical(
        [
            RankedChunkHit(active_chunk.id, 1, 0.9),
            RankedChunkHit(inactive_chunk.id, 2, 0.8),
            RankedChunkHit(failed_chunk.id, 3, 0.7),
            RankedChunkHit(wrong_chunk.id, 4, 0.6),
        ]
    )
    semantic = FakeSemantic([RankedChunkHit(active_chunk.id, 1, 0.9)])
    scope = await ConversationScopeService(db_session).get_queryable_scope(
        user=user,
        conversation_id=conv.id,
    )
    retriever = HybridRetriever(db_session, lexical=lexical, semantic=semantic)

    result = await retriever.retrieve(
        user_id=user.id,
        scope=scope,
        query="refund",
        settings=settings,
    )

    assert [c.chunk_id for c in result.chunks] == [active_chunk.id]
    assert result.chunks[0].filename == "ready.pdf"
