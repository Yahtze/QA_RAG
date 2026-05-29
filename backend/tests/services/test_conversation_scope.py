import pytest

from app.models import Conversation, Document, DocumentStatus, User
from app.services.conversation_errors import ForbiddenError, InvalidStateError, NotFoundError
from app.services.conversation_scope import ConversationScopeService


async def make_user(db_session, email="u@example.com"):
    user = User(email=email, hashed_password="x", name="User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def make_doc(db_session, user, filename="a.pdf", status=DocumentStatus.READY.value):
    doc = Document(
        user_id=user.id,
        filename=filename,
        content_type="application/pdf",
        size_bytes=10,
        storage_path=f"uploads/{user.id}/{filename}",
        status=status,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_create_scope_defaults_to_document_id(db_session):
    user = await make_user(db_session)
    doc = await make_doc(db_session, user)
    scope = ConversationScopeService(db_session)

    conv = await scope.create_conversation(user=user, document_id=doc.id, active_document_ids=[])

    assert conv.document_id == doc.id
    assert conv.active_document_ids == [str(doc.id)]


@pytest.mark.asyncio
async def test_update_active_docs_rejects_wrong_user_and_not_ready(db_session):
    user = await make_user(db_session, "owner@example.com")
    other = await make_user(db_session, "other@example.com")
    ready = await make_doc(db_session, user, "ready.pdf")
    failed = await make_doc(db_session, user, "failed.pdf", DocumentStatus.FAILED.value)
    wrong_user = await make_doc(db_session, other, "wrong.pdf")
    conv = Conversation(user_id=user.id, document_id=ready.id, active_document_ids=[str(ready.id)])
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)
    scope = ConversationScopeService(db_session)

    with pytest.raises(ForbiddenError):
        await scope.update_active_documents(
            user=user, conversation_id=conv.id, active_document_ids=[wrong_user.id]
        )
    with pytest.raises(InvalidStateError):
        await scope.update_active_documents(
            user=user, conversation_id=conv.id, active_document_ids=[failed.id]
        )


@pytest.mark.asyncio
async def test_queryable_ready_documents_never_falls_back(db_session):
    user = await make_user(db_session)
    ready = await make_doc(db_session, user, "ready.pdf")
    inactive = await make_doc(db_session, user, "inactive.pdf")
    conv = Conversation(user_id=user.id, document_id=ready.id, active_document_ids=[])
    db_session.add(conv)
    await db_session.commit()
    scope = ConversationScopeService(db_session)

    result = await scope.get_queryable_scope(user=user, conversation_id=conv.id)

    assert result.conversation_id == conv.id
    assert result.active_document_ids == []
    assert result.ready_document_ids == []
    assert inactive.id not in result.ready_document_ids


@pytest.mark.asyncio
async def test_scope_ownership_validation(db_session):
    owner = await make_user(db_session, "owner2@example.com")
    other = await make_user(db_session, "other2@example.com")
    doc = await make_doc(db_session, owner)
    conv = Conversation(user_id=owner.id, document_id=doc.id, active_document_ids=[str(doc.id)])
    db_session.add(conv)
    await db_session.commit()
    scope = ConversationScopeService(db_session)

    with pytest.raises(ForbiddenError):
        await scope.get_queryable_scope(user=other, conversation_id=conv.id)
    with pytest.raises(NotFoundError):
        await scope.get_queryable_scope(user=owner, conversation_id=doc.id)
