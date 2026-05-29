.PHONY: dev build docker-up docker-down docker-logs lint clean

dev:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f frontend

lint:
	cd frontend && npm run lint

clean:
	rm -rf frontend/node_modules frontend/dist frontend/.env
