import json
import uuid
from uuid import uuid4

import pytest

from app.models import Conversation, Document, DocumentChunk, DocumentStatus


@pytest.mark.asyncio
async def test_stream_endpoint_returns_sse_events(
    async_client,
    auth_headers,
    db_session,
    monkeypatch,
):
    user = (await async_client.get("/api/v1/auth/me", headers=auth_headers)).json()
    user_id = uuid.UUID(user["id"])
    doc = Document(
        user_id=user_id,
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
        page=1,
        chunk_index=0,
        char_start=0,
        char_end=15,
        text="Refunds five days",
        text_hash="h",
        embedding_model="m",
    )
    db_session.add(chunk)
    conv = Conversation(
        user_id=user_id, document_id=doc.id, active_document_ids=[str(doc.id)]
    )
    db_session.add(conv)
    await db_session.commit()

    class FakePipeline:
        async def answer(self, **kwargs):
            from app.services.answer_pipeline import AnswerEvent

            yield AnswerEvent(type="token", value="Answer")
            yield AnswerEvent(
                type="citations",
                map={
                    "1": {
                        "chunk_id": str(chunk.id),
                        "doc_id": str(doc.id),
                        "filename": "guide.pdf",
                        "page": 1,
                        "snippet": "Refunds five days",
                    }
                },
            )
            yield AnswerEvent(type="done")

    monkeypatch.setattr(
        "app.api.v1.conversations.build_answer_pipeline",
        lambda session, settings: FakePipeline(),
    )

    response = await async_client.post(
        f"/api/v1/conversations/{conv.id}/messages/stream",
        headers=auth_headers,
        json={"content": "Refunds?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    lines = [
        line.removeprefix("data: ")
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert [json.loads(line)["type"] for line in lines] == [
        "token",
        "citations",
        "done",
    ]


@pytest.mark.asyncio
async def test_active_scope_endpoint_updates_conversation(
    async_client, auth_headers, db_session
):
    user = (await async_client.get("/api/v1/auth/me", headers=auth_headers)).json()
    user_id = uuid.UUID(user["id"])
    doc = Document(
        user_id=user_id,
        filename="guide.pdf",
        content_type="application/pdf",
        size_bytes=1,
        storage_path="guide",
        status=DocumentStatus.READY.value,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    conv_response = await async_client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"document_id": str(doc.id)},
    )
    conv_id = conv_response.json()["id"]

    response = await async_client.put(
        f"/api/v1/conversations/{conv_id}/active-documents",
        headers=auth_headers,
        json={"active_document_ids": []},
    )

    assert response.status_code == 200
    assert response.json()["active_document_ids"] == []
