import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.models import Conversation, Message, MessageRole, User
from app.services.citation_mapper import citation_rows, citations_event_map
from app.services.context_packer import pack_context
from app.services.conversation_errors import ForbiddenError, NotFoundError
from app.services.conversation_scope import ConversationScopeService
from app.services.prompt_builder import HistoryTurn, build_grounded_messages
from app.services.retrieval_types import RetrievalResult
from app.services.semantic_cache import RedisSemanticCache

logger = logging.getLogger(__name__)

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
        semantic_cache: RedisSemanticCache | None = None,
    ):
        self.session = session
        self.settings = settings
        self.retriever = retriever
        self.llm = llm
        self.semantic_cache = semantic_cache

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

        cache_hit = await self._semantic_cache_get(content)
        if cache_hit is not None:
            assistant = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT.value,
                content=cache_hit.answer,
            )
            self.session.add(assistant)
            await self.session.commit()
            yield AnswerEvent(type="token", value=cache_hit.answer)
            yield AnswerEvent(type="citations", map=cache_hit.citations)
            yield AnswerEvent(type="done")
            return

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
                reason=(
                    str(result.no_context_reason) if result.no_context_reason else None
                ),
            )
            yield AnswerEvent(type="citations", map={})
            yield AnswerEvent(type="done")
            return

        packed = pack_context(
            result,
            final_top_k=self.settings.RETRIEVAL_FINAL_TOP_K,
            max_chars=self.settings.CONTEXT_MAX_CHARS,
        )
        history = await self._build_history(conversation_id)
        messages = build_grounded_messages(
            question=content,
            context_text=packed.context_text,
            history=history,
        )

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
        self.session.add_all(
            citation_rows(message_id=assistant.id, chunks=packed.chunks)
        )
        await self.session.commit()

        citation_map = citations_event_map(packed.chunks)
        self._semantic_cache_set_async(
            query=content,
            answer="".join(answer_parts),
            citations=citation_map,
        )

        yield AnswerEvent(type="citations", map=citation_map)
        yield AnswerEvent(type="done")

    async def _semantic_cache_get(self, query: str):
        if not self.settings.SEMANTIC_CACHE_ENABLED or self.semantic_cache is None:
            return None
        try:
            hit = await self.semantic_cache.get(query=query)
            if hit is None:
                logger.info("semantic_cache_pipeline_lookup", extra={"hit": False})
            else:
                logger.info("semantic_cache_pipeline_lookup", extra={"hit": True})
            return hit
        except TimeoutError:
            logger.warning("semantic_cache_pipeline_lookup_fallback reason=timeout")
            return None
        except Exception as exc:
            logger.warning(
                "semantic_cache_pipeline_lookup_fallback reason=error error=%s",
                str(exc),
            )
            return None

    def _semantic_cache_set_async(
        self,
        *,
        query: str,
        answer: str,
        citations: dict[str, dict[str, object]],
    ) -> None:
        if not self.settings.SEMANTIC_CACHE_ENABLED or self.semantic_cache is None:
            return

        async def _write() -> None:
            try:
                await self.semantic_cache.set(
                    query=query,
                    answer=answer,
                    citations=citations,
                )
                logger.info("semantic_cache_pipeline_write", extra={"status": "ok"})
            except TimeoutError:
                logger.warning("semantic_cache_pipeline_write status=timeout")
                return
            except Exception as exc:
                logger.warning(
                    "semantic_cache_pipeline_write status=error error=%s",
                    str(exc),
                )
                return

        asyncio.create_task(_write())

    async def _build_history(self, conversation_id: UUID) -> list[HistoryTurn]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.error_message.is_(None))
            .options(selectinload(Message.citations))
            .order_by(Message.created_at, Message.id)
        )
        messages = result.scalars().all()

        turns: list[HistoryTurn] = []
        pending_question: str | None = None

        for msg in messages:
            if msg.role == MessageRole.USER.value:
                pending_question = msg.content
            elif (
                msg.role == MessageRole.ASSISTANT.value and pending_question is not None
            ):
                ctx_parts: list[str] = []
                for citation in msg.citations:
                    page = f" p.{citation.page_number}" if citation.page_number else ""
                    label = citation.label or "?"
                    ctx_parts.append(
                        f"[{label}] {citation.filename}{page}\n{citation.chunk_text.strip()}"
                    )
                context_text = "\n\n".join(ctx_parts) if ctx_parts else "(no context)"
                turns.append(
                    HistoryTurn(
                        question=pending_question,
                        context_text=context_text,
                        answer=msg.content,
                    )
                )
                pending_question = None

        return turns
