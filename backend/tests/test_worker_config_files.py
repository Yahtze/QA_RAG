from pathlib import Path


def test_makefile_has_backend_worker_target():
    text = Path("Makefile").read_text()
    assert "backend-worker:" in text
    assert "celery -A app.worker.celery_app worker" in text
    assert "--max-tasks-per-child=$${CELERY_MAX_TASKS_PER_CHILD:-50}" in text


def test_docker_compose_has_worker_service():
    text = Path("docker-compose.yml").read_text()
    assert "worker:" in text
    assert "celery" in text
    assert "-Q ingestion" in text
    assert "CELERY_WORKER_CONCURRENCY" in text
