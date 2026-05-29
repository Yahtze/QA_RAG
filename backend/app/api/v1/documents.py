from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings_dep
from app.core.pagination import CursorPage
from app.db.session import get_db_session
from app.schemas.document import DocumentOut
from app.services.document_pipeline import DocumentPipelineService, ForbiddenError, NotFoundError
from app.services.storage import (
    DisallowedContentTypeError,
    InvalidPdfError,
    LocalStorageService,
    UploadTooLargeError,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings_dep),
):
    service = DocumentPipelineService(session, LocalStorageService(settings))
    try:
        return await service.upload(user=user, upload_file=file)
    except UploadTooLargeError:
        raise HTTPException(status_code=413, detail="Upload too large")
    except (DisallowedContentTypeError, InvalidPdfError):
        raise HTTPException(status_code=422, detail="Invalid file")


@router.get("", response_model=CursorPage[DocumentOut])
async def list_documents(
    cursor: str | None = Query(default=None),
    limit: int | None = Query(default=None),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings_dep),
):
    return await DocumentPipelineService(session, LocalStorageService(settings)).list(
        user=user, cursor=cursor, limit=limit
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings_dep),
):
    try:
        return await DocumentPipelineService(session, LocalStorageService(settings)).get(
            user=user, document_id=document_id
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings_dep),
):
    try:
        await DocumentPipelineService(session, LocalStorageService(settings)).delete(
            user=user, document_id=document_id
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
