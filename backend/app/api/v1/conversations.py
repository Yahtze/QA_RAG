from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.pagination import CursorPage
from app.db.session import get_db_session
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
    MessagePairOut,
)
from app.services.conversation import ConversationService
from app.services.conversation_errors import ForbiddenError, InvalidStateError, NotFoundError

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await ConversationService(session).create(user=user, document_id=data.document_id)
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
    return await ConversationService(session).list(user=user, cursor=cursor, limit=limit)


@router.post("/{conversation_id}/messages", response_model=MessagePairOut)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await ConversationService(session).send_message(
            user=user, conversation_id=conversation_id, content=data.content
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")


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
            user=user, conversation_id=conversation_id, cursor=cursor, limit=limit
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
