.PHONY: setup dev dev-backend dev-frontend test lint typecheck migrate gen-api infra-up infra-down

# ==========================================
# FlashCard Makefile
# ==========================================

setup:
	cp .env.example backend/.env
	cd frontend && npm install
	cd backend && pip install -e ".[dev]"
	docker compose -f infra/docker/docker-compose.yml up -d

dev:
	docker compose -f infra/docker/docker-compose.yml up -d
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npx expo start

test:
	cd backend && pytest
	cd frontend && npx jest --watchAll=false

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npx jest --watchAll=false

lint:
	cd backend && ruff check .
	cd frontend && npx eslint src --ext .ts,.tsx

lint-fix:
	cd backend && ruff check . --fix
	cd frontend && npx eslint src --ext .ts,.tsx --fix

typecheck:
	cd backend && mypy app
	cd frontend && npx tsc --noEmit

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(name)"

gen-api:
	npx @openapitools/openapi-generator-cli generate \
		-i contract/openapi.yaml \
		-g typescript-fetch \
		-o frontend/src/api/generated

infra-up:
	docker compose -f infra/docker/docker-compose.yml up -d

infra-down:
	docker compose -f infra/docker/docker-compose.yml down

infra-logs:
	docker compose -f infra/docker/docker-compose.yml logs -f
