import uuid

import pytest


@pytest.mark.asyncio
async def test_conversation_flow(async_client, auth_headers, monkeypatch, db_session):
    from app.services.ingestion_queue import FakeIngestionQueue
    from app.models.document import Document
    from sqlalchemy import select

    q = FakeIngestionQueue()
    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: q)

    files = {"file": ("doc.txt", b"hello world", "text/plain")}
    up = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    doc_id = up.json()["id"]
    assert up.json()["status"] == "pending"

    # Manually mark document as ready so conversation can be created
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    doc.status = "ready"
    await db_session.commit()

    conv = await async_client.post(
        "/api/v1/conversations", json={"document_id": doc_id}, headers=auth_headers
    )
    assert conv.status_code == 201
    conv_id = conv.json()["id"]

    msg = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "hello"},
        headers=auth_headers,
    )
    assert msg.status_code == 200
    assert msg.json()["assistant_message"]["content"].startswith("This is a placeholder")

    history = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages", headers=auth_headers
    )
    assert history.status_code == 200
    assert len(history.json()["items"]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["pending", "processing", "failed"])
async def test_conversation_rejects_non_ready_documents(async_client, auth_headers, monkeypatch, db_session, status):
    from app.services.ingestion_queue import FakeIngestionQueue
    from app.models.document import Document
    from app.models.user import User
    from sqlalchemy import select

    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: FakeIngestionQueue())

    files = {"file": ("doc.txt", b"hello", "text/plain")}
    up = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    doc_id = up.json()["id"]

    # Manually set the document status
    user = (await db_session.execute(select(User).where(User.email == "user@example.com"))).scalar_one()
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    doc.status = status
    await db_session.commit()

    r = await async_client.post(
        "/api/v1/conversations",
        json={"document_id": doc_id},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid document state"
