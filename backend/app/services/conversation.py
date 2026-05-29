from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pagination import (
    build_cursor_predicate,
    decode_cursor,
    normalize_limit,
    page_from_items,
)
from app.models import Citation, Conversation, Document, DocumentStatus, Message, MessageRole, User
from app.schemas.conversation import CitationOut, ConversationOut, MessageOut, MessagePairOut

ASSISTANT_STUB = "This is a placeholder answer generated before RAG ingestion is implemented."
CITATION_STUB = "Stub citation text for frontend wiring."


class NotFoundError(Exception): ...


class ForbiddenError(Exception): ...


class InvalidStateError(Exception): ...


class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, user: User, document_id):
        doc = (
            await self.session.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()
        if not doc:
            raise NotFoundError
        if doc.user_id != user.id:
            raise ForbiddenError
        if doc.status != DocumentStatus.READY.value:
            raise InvalidStateError
        c = Conversation(user_id=user.id, document_id=document_id)
        self.session.add(c)
        await self.session.commit()
        await self.session.refresh(c)
        return ConversationOut.model_validate(c, from_attributes=True)

    async def list(self, *, user: User, cursor: str | None, limit: int | None):
        lim = normalize_limit(limit)
        cur = decode_cursor(cursor)
        q = select(Conversation).where(Conversation.user_id == user.id)
        pred = build_cursor_predicate(Conversation.created_at, Conversation.id, cur)
        if pred is not None:
            q = q.where(pred)
        q = q.order_by(Conversation.created_at, Conversation.id).limit(lim + 1)
        items = list((await self.session.execute(q)).scalars().all())
        out = [ConversationOut.model_validate(x, from_attributes=True) for x in items]
        return page_from_items(
            out, lim, lambda d: type("C", (), {"created_at": d.created_at, "id": d.id})()
        )

    async def send_message(self, *, user: User, conversation_id, content: str):
        conv = (
            await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
        ).scalar_one_or_none()
        if not conv:
            raise NotFoundError
        if conv.user_id != user.id:
            raise ForbiddenError
        user_m = Message(conversation_id=conv.id, role=MessageRole.USER.value, content=content)
        bot_m = Message(
            conversation_id=conv.id, role=MessageRole.ASSISTANT.value, content=ASSISTANT_STUB
        )
        self.session.add_all([user_m, bot_m])
        await self.session.flush()
        cit = Citation(
            message_id=bot_m.id,
            document_id=conv.document_id,
            chunk_text=CITATION_STUB,
            page_number=1,
            score=0.0,
        )
        self.session.add(cit)
        await self.session.commit()
        await self.session.refresh(user_m)
        await self.session.refresh(bot_m)
        await self.session.refresh(cit)
        return MessagePairOut(
            user_message=MessageOut(
                id=user_m.id,
                role="user",
                content=user_m.content,
                created_at=user_m.created_at,
                citations=[],
            ),
            assistant_message=MessageOut(
                id=bot_m.id,
                role="assistant",
                content=bot_m.content,
                created_at=bot_m.created_at,
                citations=[CitationOut.model_validate(cit, from_attributes=True)],
            ),
        )

    async def messages(self, *, user: User, conversation_id, cursor: str | None, limit: int | None):
        conv = (
            await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
        ).scalar_one_or_none()
        if not conv:
            raise NotFoundError
        if conv.user_id != user.id:
            raise ForbiddenError
        lim = normalize_limit(limit)
        cur = decode_cursor(cursor)
        q = (
            select(Message)
            .options(selectinload(Message.citations))
            .where(Message.conversation_id == conv.id)
        )
        pred = build_cursor_predicate(Message.created_at, Message.id, cur)
        if pred is not None:
            q = q.where(pred)
        q = q.order_by(Message.created_at, Message.id).limit(lim + 1)
        msgs = list((await self.session.execute(q)).scalars().all())

        def map_msg(m: Message) -> MessageOut:
            return MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
                citations=[
                    CitationOut.model_validate(c, from_attributes=True) for c in m.citations
                ],
            )

        out = [map_msg(m) for m in msgs]
        return page_from_items(
            out, lim, lambda d: type("C", (), {"created_at": d.created_at, "id": d.id})()
        )
