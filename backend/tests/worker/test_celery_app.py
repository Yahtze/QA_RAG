from app.worker.celery_app import celery_app


def test_celery_config(settings):
    assert celery_app.conf.task_ignore_result is True
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.task_routes["documents.ingest"] == {"queue": "ingestion"}
