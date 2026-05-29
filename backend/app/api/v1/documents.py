from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings_dep
from app.core.pagination import CursorPage
from app.db.session import get_db_session
from app.schemas.document import DeletedDocumentOut, DocumentOut
from app.services.async_document_upload import AsyncDocumentUpload, ENQUEUE_FAILURE_MESSAGE
from app.services.document_pipeline import DocumentPipelineService, ForbiddenError, NotFoundError
from app.services.ingestion_factory import build_ingestion_service
from app.services.ingestion_queue import CeleryIngestionQueue, EnqueueIngestionError
from app.services.storage import (
    DisallowedContentTypeError,
    InvalidPdfError,
    LocalStorageService,
    UploadTooLargeError,
)
from app.services.vector_store import QdrantVectorStore

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings_dep),
):
    try:
        if settings.USE_ASYNC_INGESTION:
            return await AsyncDocumentUpload(
                session=session,
                settings=settings,
                queue=CeleryIngestionQueue(settings=settings),
            ).upload(user=user, upload_file=file)
        storage = LocalStorageService(settings)
        service = DocumentPipelineService(
            session,
            storage,
            ingestion_service=build_ingestion_service(session=session, settings=settings),
            vector_store=QdrantVectorStore(settings),
        )
        return await service.upload(user=user, upload_file=file)
    except EnqueueIngestionError:
        raise HTTPException(status_code=500, detail=ENQUEUE_FAILURE_MESSAGE)
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


@router.delete("/{document_id}", response_model=DeletedDocumentOut, status_code=200)
async def delete_document(
    document_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings_dep),
):
    try:
        service = DocumentPipelineService(
            session, LocalStorageService(settings), vector_store=QdrantVectorStore(settings)
        )
        return await service.delete(user=user, document_id=document_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except ForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden")
