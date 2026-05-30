import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings_dep
from app.core.config import Settings
from app.core.pagination import CursorPage
from app.db.session import get_db_session
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationScopeUpdate,
    MessageCreate,
    MessageOut,
    MessagePairOut,
)
from app.services.answer_pipeline import AnswerEvent, AnswerPipeline
from app.services.conversation import ConversationService
from app.services.conversation_errors import (
    ForbiddenError,
    InvalidStateError,
    NotFoundError,
)
from app.services.conversation_scope import ConversationScopeService
from app.services.embeddings import OpenAIEmbeddingProvider
from app.services.hybrid_retrieval import HybridRetriever
from app.services.lexical_retriever import LexicalRetriever
from app.services.llm_provider import OpenAICompatibleLLMProvider
from app.services.semantic_cache import RedisSemanticCache
from app.services.semantic_chunk_search import QdrantSemanticChunkSearch
from app.services.vector_store import QdrantVectorStore

router = APIRouter(prefix="/conversations", tags=["conversations"])


def build_answer_pipeline(session: AsyncSession, settings: Settings) -> AnswerPipeline:
    lexical = LexicalRetriever(session)
    embeddings = OpenAIEmbeddingProvider(settings)
    semantic = QdrantSemanticChunkSearch(
        settings=settings,
        embeddings=embeddings,
    )
    retriever = HybridRetriever(session, lexical=lexical, semantic=semantic)
    llm = OpenAICompatibleLLMProvider(settings)
    semantic_cache = RedisSemanticCache(settings, embeddings)
    vector_store = QdrantVectorStore(settings)
    return AnswerPipeline(
        session,
        settings=settings,
        retriever=retriever,
        llm=llm,
        semantic_cache=semantic_cache,
        vector_store=vector_store,
    )


def event_payload(event: AnswerEvent) -> dict:
    if event.type == "token":
        payload = {"type": "token", "value": event.value or ""}
        if event.reason:
            payload["reason"] = event.reason
        return payload
    if event.type == "citations":
        return {"type": "citations", "map": event.map or {}}
    if event.type == "error":
        return {
            "type": "error",
            "message": event.message or "The assistant could not answer this question.",
            "retryable": event.retryable is not False,
        }
    return {"type": "done"}


async def sse_stream(events: AsyncIterator[AnswerEvent]) -> AsyncIterator[str]:
    async for event in events:
        yield f"data: {json.dumps(event_payload(event))}\n\n"


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await ConversationService(session).create(
            user=user,
            document_id=data.document_id,
            active_document_ids=data.active_document_ids,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except InvalidStateError:
        raise HTTPException(status_code=400, detail="Invalid document state")


@router.get("", response_model=CursorPage[ConversationOut])
async def list_conversations(
    cursor: str | None = Query(default=None),
    limit: int | None = Query(default=None),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await ConversationService(session).list(
        user=user, cursor=cursor, limit=limit
    )


@router.put("/{conversation_id}/active-documents", response_model=ConversationOut)
async def update_active_documents(
    conversation_id: UUID,
    data: ConversationScopeUpdate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        conv = await ConversationScopeService(session).update_active_documents(
            user=user,
            conversation_id=conversation_id,
            active_document_ids=data.active_document_ids,
        )
        return ConversationService(session)._conversation_out(conv)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except InvalidStateError:
        raise HTTPException(status_code=400, detail="Invalid document state")


@router.post("/{conversation_id}/messages", response_model=MessagePairOut)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
):
    try:
        pipeline = build_answer_pipeline(session, settings)
        return await ConversationService(
            session, answer_pipeline=pipeline
        ).send_message(
            user=user,
            conversation_id=conversation_id,
            content=data.content,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except InvalidStateError:
        raise HTTPException(status_code=400, detail="Invalid document state")


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: UUID,
    data: MessageCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
):
    pipeline = build_answer_pipeline(session, settings)
    return StreamingResponse(
        sse_stream(
            pipeline.answer(
                user=user,
                conversation_id=conversation_id,
                content=data.content,
            )
        ),
        media_type="text/event-stream",
    )


@router.get("/{conversation_id}/messages", response_model=CursorPage[MessageOut])
async def list_messages(
    conversation_id: UUID,
    cursor: str | None = Query(default=None),
    limit: int | None = Query(default=None),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await ConversationService(session).messages(
            user=user,
            conversation_id=conversation_id,
            cursor=cursor,
            limit=limit,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
