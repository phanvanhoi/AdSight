.PHONY: dev stop build logs restart shell migrate seed init-es test test-frontend test-all lint lint-fix setup

# Development
dev:
	docker compose up -d

stop:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f celery-worker

restart:
	docker compose restart

# Backend shell
shell:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U adsight -d adsight

# Database
migrate:
	cd backend && alembic upgrade head

migrate-docker:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

# Elasticsearch
init-es:
	cd backend && python -m scripts.init_es

init-es-docker:
	docker compose exec api python -m scripts.init_es

# Data
seed:
	cd backend && python -m scripts.seed_data

seed-docker:
	docker compose exec api python -m scripts.seed_data

collect-meta:
	docker compose exec api python -m app.collectors.meta_collector

collect-tiktok:
	docker compose exec api python -m app.collectors.tiktok_collector

collect-google:
	docker compose exec api python -c "import asyncio; from app.collectors.google_collector import collect_and_store; asyncio.run(collect_and_store())"

collect-tiktok-shop:
	docker compose exec api python -c "import asyncio; from app.collectors.tiktok_shop_crawler import collect_and_store; asyncio.run(collect_and_store())"

crawl-pages:
	docker compose exec api python -m scripts.run_task crawl-pages

download-creatives:
	docker compose exec api python -m scripts.run_task download-creatives

match-advertisers:
	docker compose exec api python -m scripts.run_task match-advertisers

# Testing
test:
	cd backend && pytest tests/ -v --tb=short

test-frontend:
	cd frontend && npm run test:run

test-all: test test-frontend

# Linting
lint:
	cd backend && ruff check . && ruff format --check .

lint-fix:
	cd backend && ruff check --fix . && ruff format .

# Frontend
fe-shell:
	docker compose exec frontend sh

fe-install:
	docker compose exec frontend npm install

# Setup (first time)
setup: build init-es-docker migrate-docker seed-docker
	@echo "Setup complete! Run 'make dev' to start."
