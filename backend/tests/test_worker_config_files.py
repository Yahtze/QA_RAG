from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_makefile_has_backend_worker_target():
    text = (REPO_ROOT / "Makefile").read_text()
    assert "backend-worker:" in text
    assert "celery -A app.worker.celery_app worker" in text
    assert "--max-tasks-per-child=$${CELERY_MAX_TASKS_PER_CHILD:-50}" in text


def test_docker_compose_has_worker_service():
    text = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "worker:" in text
    assert "celery" in text
    assert "-Q ingestion" in text
    assert "CELERY_WORKER_CONCURRENCY" in text
