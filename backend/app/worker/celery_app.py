from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "qa_rag",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)
celery_app.conf.update(
    task_ignore_result=settings.CELERY_TASK_IGNORE_RESULT,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={"documents.ingest": {"queue": "ingestion"}},
)
