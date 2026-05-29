from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Document, DocumentStatus, User
from app.services.conversation_errors import ForbiddenError, InvalidStateError, NotFoundError


@dataclass(frozen=True)
class QueryableConversationScope:
    conversation_id: UUID
    user_id: UUID
    active_document_ids: list[UUID]
    ready_document_ids: list[UUID]
    filenames_by_document_id: dict[UUID, str]


class ConversationScopeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(
        self,
        *,
        user: User,
        document_id: UUID | None,
        active_document_ids: list[UUID],
    ) -> Conversation:
        ids = list(dict.fromkeys(active_document_ids or ([document_id] if document_id else [])))
        await self._validate_documents(user=user, document_ids=ids, require_ready=True)
        conv = Conversation(
            user_id=user.id,
            document_id=document_id or (ids[0] if ids else None),
            active_document_ids=[str(x) for x in ids],
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def update_active_documents(
        self,
        *,
        user: User,
        conversation_id: UUID,
        active_document_ids: list[UUID],
    ) -> Conversation:
        conv = await self._get_owned_conversation(user=user, conversation_id=conversation_id)
        ids = list(dict.fromkeys(active_document_ids))
        await self._validate_documents(user=user, document_ids=ids, require_ready=True)
        conv.active_document_ids = [str(x) for x in ids]
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get_queryable_scope(
        self,
        *,
        user: User,
        conversation_id: UUID,
    ) -> QueryableConversationScope:
        conv = await self._get_owned_conversation(user=user, conversation_id=conversation_id)
        active_ids = [UUID(str(x)) for x in (conv.active_document_ids or [])]
        if not active_ids:
            return QueryableConversationScope(conv.id, user.id, [], [], {})

        rows = list(
            (
                await self.session.execute(
                    select(Document).where(
                        Document.user_id == user.id,
                        Document.id.in_(active_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        ready = [doc for doc in rows if doc.status == DocumentStatus.READY.value]
        return QueryableConversationScope(
            conversation_id=conv.id,
            user_id=user.id,
            active_document_ids=active_ids,
            ready_document_ids=[doc.id for doc in ready],
            filenames_by_document_id={doc.id: doc.filename for doc in ready},
        )

    async def _get_owned_conversation(
        self,
        *,
        user: User,
        conversation_id: UUID,
    ) -> Conversation:
        conv = (
            await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
        ).scalar_one_or_none()
        if conv is None:
            raise NotFoundError
        if conv.user_id != user.id:
            raise ForbiddenError
        return conv

    async def _validate_documents(
        self,
        *,
        user: User,
        document_ids: list[UUID],
        require_ready: bool,
    ) -> None:
        if not document_ids:
            return
        docs = list(
            (
                await self.session.execute(
                    select(Document).where(Document.id.in_(document_ids))
                )
            )
            .scalars()
            .all()
        )
        by_id = {doc.id: doc for doc in docs}
        for document_id in document_ids:
            doc = by_id.get(document_id)
            if doc is None:
                raise NotFoundError
            if doc.user_id != user.id:
                raise ForbiddenError
            if require_ready and doc.status != DocumentStatus.READY.value:
                raise InvalidStateError
