from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pagination import (
    build_cursor_predicate,
    decode_cursor,
    normalize_limit,
    page_from_items,
)
from app.models import Conversation, Message, MessageRole, User
from app.schemas.conversation import ConversationOut, MessageOut, MessagePairOut, CitationOut
from app.services.conversation_errors import ForbiddenError, InvalidStateError, NotFoundError
from app.services.conversation_scope import ConversationScopeService


class ConversationService:
    def __init__(self, session: AsyncSession, answer_pipeline=None):
        self.session = session
        self.answer_pipeline = answer_pipeline

    def _conversation_out(
        self,
        conv: Conversation,
        dangling_user_message_id: UUID | None = None,
    ) -> ConversationOut:
        return ConversationOut(
            id=conv.id,
            document_id=conv.document_id,
            active_document_ids=[UUID(str(x)) for x in (conv.active_document_ids or [])],
            dangling_user_message_id=dangling_user_message_id,
            needs_retry=dangling_user_message_id is not None,
            created_at=conv.created_at,
        )

    async def _dangling_user_message_id(self, conv_id: UUID) -> UUID | None:
        q = (
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
        )
        latest = (await self.session.execute(q)).scalar_one_or_none()
        if latest is None:
            return None
        if latest.role == MessageRole.USER.value:
            return latest.id
        if latest.role == MessageRole.ASSISTANT.value and latest.retryable:
            return latest.id
        return None

    async def create(self, *, user: User, document_id, active_document_ids: list | None = None):
        conv = await ConversationScopeService(self.session).create_conversation(
            user=user,
            document_id=document_id,
            active_document_ids=active_document_ids or [],
        )
        return self._conversation_out(conv, dangling_user_message_id=None)

    async def list(self, *, user: User, cursor: str | None, limit: int | None):
        lim = normalize_limit(limit)
        cur = decode_cursor(cursor)
        q = select(Conversation).where(Conversation.user_id == user.id)
        pred = build_cursor_predicate(Conversation.created_at, Conversation.id, cur)
        if pred is not None:
            q = q.where(pred)
        q = q.order_by(Conversation.created_at, Conversation.id).limit(lim + 1)
        items = list((await self.session.execute(q)).scalars().all())

        out: list[ConversationOut] = []
        for conv in items:
            out.append(
                self._conversation_out(
                    conv,
                    dangling_user_message_id=await self._dangling_user_message_id(conv.id),
                )
            )

        return page_from_items(
            out,
            lim,
            lambda d: type("C", (), {"created_at": d.created_at, "id": d.id})(),
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
        if self.answer_pipeline is None:
            raise InvalidStateError

        async for event in self.answer_pipeline.answer(
            user=user,
            conversation_id=conversation_id,
            content=content,
        ):
            if event.type == "error":
                raise InvalidStateError

        history = await self.messages(
            user=user,
            conversation_id=conversation_id,
            cursor=None,
            limit=2,
        )
        if len(history.items) < 2:
            raise InvalidStateError
        return MessagePairOut(
            user_message=history.items[-2],
            assistant_message=history.items[-1],
        )

    async def messages(
        self,
        *,
        user: User,
        conversation_id,
        cursor: str | None,
        limit: int | None,
    ):
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
            out,
            lim,
            lambda d: type("C", (), {"created_at": d.created_at, "id": d.id})(),
        )
