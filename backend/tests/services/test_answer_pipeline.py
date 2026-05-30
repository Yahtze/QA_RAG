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
