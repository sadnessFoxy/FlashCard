.PHONY: setup dev worker dev-backend dev-frontend test test-backend test-frontend lint lint-fix typecheck migrate migrate-create gen-api infra-up infra-down infra-logs

# ==========================================
# FlashCard Makefile
# Backend runs in the backend/.venv virtualenv
# ==========================================

ifeq ($(OS),Windows_NT)
VENV_BIN := .venv/Scripts
else
VENV_BIN := .venv/bin
endif
PY := $(VENV_BIN)/python
COMPOSE := docker compose -f infra/docker/docker-compose.yml

setup:
	@test -f backend/.env || cp .env.example backend/.env
	cd frontend && npm install
	cd backend && (test -d .venv || python -m venv .venv) && $(PY) -m pip install -e ".[dev]"
	$(COMPOSE) up -d

dev:
	$(COMPOSE) up -d
	$(MAKE) -j3 dev-backend worker dev-frontend

worker:
	cd backend && $(PY) -m arq app.workers.queue.WorkerSettings

dev-backend:
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npx expo start

test: test-backend test-frontend

test-backend:
	cd backend && $(PY) -m pytest

test-frontend:
	cd frontend && npx jest --watchAll=false --passWithNoTests

lint:
	cd backend && $(PY) -m ruff check .
	cd frontend && npx eslint src --ext .ts,.tsx

lint-fix:
	cd backend && $(PY) -m ruff check . --fix
	cd frontend && npx eslint src --ext .ts,.tsx --fix

typecheck:
	cd backend && $(PY) -m mypy app
	cd frontend && npx tsc --noEmit

migrate:
	cd backend && $(PY) -m alembic upgrade head

migrate-create:
	cd backend && $(PY) -m alembic revision --autogenerate -m "$(name)"

# Generate TypeScript types from the contract (committed)
gen-api:
	cd frontend && npm run gen-api

infra-up:
	$(COMPOSE) up -d

infra-down:
	$(COMPOSE) down

infra-logs:
	$(COMPOSE) logs -f
