import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import (
    Citation,
    Conversation,
    Document,
    DocumentChunk,
    DocumentStatus,
    Message,
    MessageRole,
    User,
)
from app.services.answer_pipeline import AnswerPipeline
from app.services.semantic_cache import SemanticCacheHit
from app.services.retrieval_types import (
    NoContextReason,
    RetrievalResult,
    RetrievedChunk,
)


class FakeRetriever:
    def __init__(self, result):
        self.result = result

    async def retrieve(self, **kwargs):
        return self.result


class FakeLLM:
    def __init__(self, tokens=None, exc=None):
        self.tokens = tokens or []
        self.exc = exc
        self.called = False

    async def stream(self, messages):
        self.called = True
        if self.exc:
            raise self.exc
        for token in self.tokens:
            yield token


class FakeSemanticCache:
    def __init__(self, hit=None):
        self.hit = hit
        self.get_called = False
        self.set_called = False
        self.set_chunk_ids = None

    async def get(self, *, query: str, document_ids=None):
        self.get_called = True
        return self.hit

    async def set(self, *, query: str, answer: str, chunk_ids: list, document_ids=None):
        self.set_called = True
        self.set_chunk_ids = chunk_ids


class FakeVectorStore:
    def __init__(self, payloads=None, exc=None):
        self.payloads = payloads or []
        self.exc = exc
        self.retrieve_called = False

    async def retrieve_by_ids(self, ids):
        self.retrieve_called = True
        if self.exc:
            raise self.exc
        return self.payloads


async def fixture(db_session):
    user = User(email="a@example.com", hashed_password="x", name="A")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    doc = Document(
        user_id=user.id,
        filename="guide.pdf",
        content_type="application/pdf",
        size_bytes=1,
        storage_path="guide",
        status=DocumentStatus.READY.value,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=doc.id,
        source="guide.pdf",
        page=2,
        chunk_index=0,
        char_start=0,
        char_end=18,
        text="Refunds: five days",
        text_hash="h",
        embedding_model="m",
    )
    db_session.add(chunk)
    conv = Conversation(
        user_id=user.id, document_id=doc.id, active_document_ids=[str(doc.id)]
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)
    return user, doc, chunk, conv


@pytest.mark.asyncio
async def test_success_stream_order_and_persistence(db_session, settings):
    user, doc, chunk, conv = await fixture(db_session)
    result = RetrievalResult(
        [RetrievedChunk(chunk.id, doc.id, "guide.pdf", 2, chunk.text, 1, None, 1, 0.5)],
        None,
    )
    pipeline = AnswerPipeline(
        db_session,
        settings=settings,
        retriever=FakeRetriever(result),
        llm=FakeLLM(["Refunds ", "take five days [1]."]),
    )

    events = [
        event
        async for event in pipeline.answer(
            user=user, conversation_id=conv.id, content="Refunds?"
        )
    ]

    assert [event.type for event in events] == ["token", "token", "citations", "done"]
    assert events[2].map["1"]["filename"] == "guide.pdf"
    rows = list((await db_session.execute(select(Message))).scalars().all())
    assert {m.role for m in rows} == {
        MessageRole.USER.value,
        MessageRole.ASSISTANT.value,
    }
    assistant_row = next(m for m in rows if m.role == MessageRole.ASSISTANT.value)
    assert assistant_row.content == "Refunds take five days [1]."
    citations = list((await db_session.execute(select(Citation))).scalars().all())
    assert citations[0].chunk_id == chunk.id
    assert citations[0].label == "1"


@pytest.mark.asyncio
async def test_no_context_skips_llm_and_persists_abstention(db_session, settings):
    user, doc, chunk, conv = await fixture(db_session)
    llm = FakeLLM(["unused"])
    pipeline = AnswerPipeline(
        db_session,
        settings=settings,
        retriever=FakeRetriever(
            RetrievalResult([], NoContextReason.NO_ACTIVE_DOCUMENTS)
        ),
        llm=llm,
    )

    events = [
        event
        async for event in pipeline.answer(
            user=user, conversation_id=conv.id, content="Refunds?"
        )
    ]

    assert llm.called is False
    assert events[0].type == "token"
    assert "active documents" in events[0].value
    assert events[1].type == "citations"
    assert events[1].map == {}
    assistant = (
        await db_session.execute(
            select(Message).where(Message.role == MessageRole.ASSISTANT.value)
        )
    ).scalar_one()
    assert "active documents" in assistant.content


@pytest.mark.asyncio
async def test_handled_llm_failure_persists_failed_assistant(db_session, settings):
    user, doc, chunk, conv = await fixture(db_session)
    result = RetrievalResult(
        [RetrievedChunk(chunk.id, doc.id, "guide.pdf", 2, chunk.text, 1, None, 1, 0.5)],
        None,
    )
    pipeline = AnswerPipeline(
        db_session,
        settings=settings,
        retriever=FakeRetriever(result),
        llm=FakeLLM(exc=RuntimeError("boom")),
    )

    events = [
        event
        async for event in pipeline.answer(
            user=user, conversation_id=conv.id, content="Refunds?"
        )
    ]

    assert events[0].type == "error"
    failed = (
        await db_session.execute(
            select(Message).where(Message.role == MessageRole.ASSISTANT.value)
        )
    ).scalar_one()
    assert failed.retryable is True
    assert failed.original_query == "Refunds?"
    assert failed.error_message == "boom"


@pytest.mark.asyncio
async def test_semantic_cache_hit_skips_retriever_and_llm(db_session, settings):
    user, doc, chunk, conv = await fixture(db_session)
    settings.SEMANTIC_CACHE_ENABLED = True
    cache = FakeSemanticCache(
        SemanticCacheHit(
            answer="Cached answer",
            chunk_ids=[str(chunk.id)],
        )
    )
    vector_store = FakeVectorStore(
        payloads=[{"document_id": str(doc.id), "text": chunk.text, "page": chunk.page}]
    )
    llm = FakeLLM(["unused"])
    pipeline = AnswerPipeline(
        db_session,
        settings=settings,
        retriever=FakeRetriever(RetrievalResult([], None)),
        llm=llm,
        semantic_cache=cache,
        vector_store=vector_store,
    )

    events = [
        event
        async for event in pipeline.answer(
            user=user, conversation_id=conv.id, content="Refunds?"
        )
    ]

    assert cache.get_called is True
    assert vector_store.retrieve_called is True
    assert llm.called is False
    assert [event.type for event in events] == ["token", "citations", "done"]
    assert events[0].value == "Cached answer"
    assert events[1].map["1"]["filename"] == "guide.pdf"


@pytest.mark.asyncio
async def test_semantic_cache_miss_writes_async(db_session, settings):
    user, doc, chunk, conv = await fixture(db_session)
    settings.SEMANTIC_CACHE_ENABLED = True
    cache = FakeSemanticCache(hit=None)
    result = RetrievalResult(
        [RetrievedChunk(chunk.id, doc.id, "guide.pdf", 2, chunk.text, 1, None, 1, 0.5)],
        None,
    )
    pipeline = AnswerPipeline(
        db_session,
        settings=settings,
        retriever=FakeRetriever(result),
        llm=FakeLLM(["Answer"]),
        semantic_cache=cache,
    )

    [
        event
        async for event in pipeline.answer(
            user=user, conversation_id=conv.id, content="Refunds?"
        )
    ]
    await asyncio.sleep(0)

    assert cache.get_called is True
    assert cache.set_called is True
    assert cache.set_chunk_ids == [str(chunk.id)]


@pytest.mark.asyncio
async def test_semantic_cache_hit_fallback_on_hydration_failure(db_session, settings):
    """When hydration fails (Qdrant error), pipeline falls back to full RAG."""
    user, doc, chunk, conv = await fixture(db_session)
    settings.SEMANTIC_CACHE_ENABLED = True
    cache = FakeSemanticCache(
        SemanticCacheHit(
            answer="Cached answer",
            chunk_ids=[str(chunk.id)],
        )
    )
    from app.services.vector_store import ChunkHydrationError

    vector_store = FakeVectorStore(exc=ChunkHydrationError("qdrant down"))
    result = RetrievalResult(
        [RetrievedChunk(chunk.id, doc.id, "guide.pdf", 2, chunk.text, 1, None, 1, 0.5)],
        None,
    )
    llm = FakeLLM(["Fresh answer"])
    pipeline = AnswerPipeline(
        db_session,
        settings=settings,
        retriever=FakeRetriever(result),
        llm=llm,
        semantic_cache=cache,
        vector_store=vector_store,
    )

    events = [
        event
        async for event in pipeline.answer(
            user=user, conversation_id=conv.id, content="Refunds?"
        )
    ]

    # Should fall back to full RAG pipeline
    assert cache.get_called is True
    assert vector_store.retrieve_called is True
    assert llm.called is True
    assert events[0].type == "token"
    assert events[0].value == "Fresh answer"
    assert events[-1].type == "done"
