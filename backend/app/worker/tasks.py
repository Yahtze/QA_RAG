import asyncio
import logging
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.services.document_ingestion_repository import DocumentIngestionRepository
from app.services.ingestion_errors import RetryableIngestionError
from app.services.ingestion_factory import build_ingestion_service
from app.services.ingestion_types import IngestionPhase
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


async def mark_final_retry_failure(
    session, document_id: UUID, exc: BaseException, max_retries: int
) -> None:
    await DocumentIngestionRepository(session).mark_failed(
        document_id,
        error_message=f"Ingestion failed after {max_retries} retries: {exc}",
        phase=IngestionPhase.DATABASE,
    )


async def run_ingestion(
    document_id: UUID | str, *, session=None, settings: Settings | None = None
) -> None:
    settings = settings or get_settings()
    document_uuid = UUID(str(document_id))
    if session is not None:
        service = build_ingestion_service(session=session, settings=settings)
        await service.ingest_document(document_uuid)
        await session.commit()
        return

    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as fresh_session:
        service = build_ingestion_service(session=fresh_session, settings=settings)
        await service.ingest_document(document_uuid)
        await fresh_session.commit()
    await engine.dispose()


async def _mark_final_retry_failure_from_settings(document_id: UUID, exc: BaseException) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        await mark_final_retry_failure(session, document_id, exc, max_retries=MAX_RETRIES)
    await engine.dispose()


class IngestionTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if self.request.retries >= MAX_RETRIES and args:
            asyncio.run(_mark_final_retry_failure_from_settings(UUID(args[0]), exc))
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    name="documents.ingest",
    base=IngestionTask,
    autoretry_for=(RetryableIngestionError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=MAX_RETRIES,
)
def ingest_document_task(document_id: str) -> None:
    logger.info("worker_task_started", extra={"document_id": document_id})
    try:
        asyncio.run(run_ingestion(UUID(document_id)))
        logger.info("worker_task_succeeded", extra={"document_id": document_id})
    except RetryableIngestionError:
        logger.warning("worker_retry_scheduled", extra={"document_id": document_id})
        raise
    except Exception:
        logger.exception("worker_task_failed", extra={"document_id": document_id})
        raise
