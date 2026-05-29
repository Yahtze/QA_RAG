from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Conversation, Message, MessageRole, User
from app.services.citation_mapper import citation_rows, citations_event_map
from app.services.context_packer import pack_context
from app.services.conversation_errors import ForbiddenError, NotFoundError
from app.services.conversation_scope import ConversationScopeService
from app.services.prompt_builder import build_grounded_messages
from app.services.retrieval_types import RetrievalResult

ABSTENTION = (
    "I don't have enough information in the active documents to answer this yet. "
    "Try selecting ready documents or uploading more relevant files."
)


@dataclass(frozen=True)
class AnswerEvent:
    type: Literal["token", "citations", "error", "done"]
    value: str | None = None
    map: dict[str, dict[str, object]] | None = None
    message: str | None = None
    retryable: bool | None = None
    reason: str | None = None


class RetrievalProvider(Protocol):
    async def retrieve(self, **kwargs) -> RetrievalResult: ...


class AnswerPipeline:
    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings,
        retriever: RetrievalProvider,
        llm,
    ):
        self.session = session
        self.settings = settings
        self.retriever = retriever
        self.llm = llm

    async def answer(
        self,
        *,
        user: User,
        conversation_id: UUID,
        content: str,
    ) -> AsyncIterator[AnswerEvent]:
        conv = (
            await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
        ).scalar_one_or_none()
        if conv is None:
            raise NotFoundError
        if conv.user_id != user.id:
            raise ForbiddenError

        scope = await ConversationScopeService(self.session).get_queryable_scope(
            user=user,
            conversation_id=conversation_id,
        )

        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )
        self.session.add(user_message)
        await self.session.commit()

        result = await self.retriever.retrieve(
            user_id=user.id,
            scope=scope,
            query=content,
            settings=self.settings,
        )

        if result.no_context_reason is not None or not result.chunks:
            assistant = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT.value,
                content=ABSTENTION,
            )
            self.session.add(assistant)
            await self.session.commit()
            yield AnswerEvent(
                type="token",
                value=ABSTENTION,
                reason=str(result.no_context_reason) if result.no_context_reason else None,
            )
            yield AnswerEvent(type="citations", map={})
            yield AnswerEvent(type="done")
            return

        packed = pack_context(
            result,
            final_top_k=self.settings.RETRIEVAL_FINAL_TOP_K,
            max_chars=self.settings.CONTEXT_MAX_CHARS,
        )
        messages = build_grounded_messages(question=content, context_text=packed.context_text)

        answer_parts: list[str] = []
        try:
            async for token in self.llm.stream(messages):
                answer_parts.append(token)
                yield AnswerEvent(type="token", value=token)
        except Exception as exc:
            failed = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT.value,
                content=str(exc),
                error_message=str(exc),
                retryable=True,
                original_query=content,
            )
            self.session.add(failed)
            await self.session.commit()
            yield AnswerEvent(type="error", message=str(exc), retryable=True)
            return

        assistant = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content="".join(answer_parts),
        )
        self.session.add(assistant)
        await self.session.flush()
        self.session.add_all(citation_rows(message_id=assistant.id, chunks=packed.chunks))
        await self.session.commit()

        yield AnswerEvent(type="citations", map=citations_event_map(packed.chunks))
        yield AnswerEvent(type="done")
