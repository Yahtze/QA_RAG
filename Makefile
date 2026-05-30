.PHONY: dev build docker-up docker-dev-up docker-down docker-logs lint clean backend-install backend-dev backend-test backend-lint backend-format backend-migrate backend-revision backend-worker

dev:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build

docker-dev-up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f frontend backend postgres redis qdrant

lint:
	cd frontend && npm run lint

clean:
	rm -rf frontend/node_modules frontend/dist frontend/.env

backend-install:
	uv pip install --python .venv/bin/python -e 'backend[dev]'

backend-dev:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

backend-test:
	.venv/bin/python -m pytest backend/tests -v

backend-lint:
	cd backend && ../.venv/bin/python -m ruff check .

backend-format:
	cd backend && ../.venv/bin/python -m ruff format .

backend-migrate:
	cd backend && ../.venv/bin/python -m alembic upgrade head

backend-revision:
	cd backend && ../.venv/bin/python -m alembic revision --autogenerate -m "$(name)"

backend-reconcile-ingestion:
	cd backend && ../.venv/bin/python -m app.cli.reconcile_ingestion

backend-reconcile-ingestion-apply:
	cd backend && ../.venv/bin/python -m app.cli.reconcile_ingestion --no-dry-run

backend-worker:
	.venv/bin/celery -A app.worker.celery_app worker -Q ingestion --loglevel=info --concurrency=$${CELERY_WORKER_CONCURRENCY:-1} --max-tasks-per-child=$${CELERY_MAX_TASKS_PER_CHILD:-50}
