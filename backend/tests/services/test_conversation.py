import pytest
from sqlalchemy import select

from app.models import Conversation, Document, DocumentStatus, User
from app.services.conversation import ConversationService


@pytest.mark.asyncio
async def test_create_send_messages(db_session):
    user = User(email="u2@example.com", hashed_password="x", name="u")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    doc = Document(
        user_id=user.id,
        filename="a.pdf",
        content_type="application/pdf",
        size_bytes=10,
        storage_path=f"uploads/{user.id}/a.pdf",
        status=DocumentStatus.READY.value,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    svc = ConversationService(db_session)
    conv = await svc.create(user=user, document_id=doc.id)
    assert conv.active_document_ids == [doc.id]
    pair = await svc.send_message(user=user, conversation_id=conv.id, content="hi")
    assert pair.assistant_message.content == "This is a placeholder answer generated before RAG ingestion is implemented."
    assert pair.assistant_message.citations[0].chunk_text == "Stub citation text for frontend wiring."

    history = await svc.messages(user=user, conversation_id=conv.id, cursor=None, limit=20)
    assert len(history.items) == 2
    rows = (await db_session.execute(select(Conversation))).scalars().all()
    assert len(rows) == 1
