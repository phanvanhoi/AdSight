.PHONY: up down build logs restart shell migrate seed init-es test lint

# Docker
up:
	docker compose up -d

up-build:
	docker compose up -d --build

down:
	docker compose down

down-clean:
	docker compose down -v

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

# Backend
shell:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U adsight -d adsight

# Database
migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

# Elasticsearch
init-es:
	docker compose exec api python -m scripts.init_es

# Data
seed:
	docker compose exec api python -m scripts.seed_data

collect-meta:
	docker compose exec api python -m app.collectors.meta_collector

collect-tiktok:
	docker compose exec api python -m app.collectors.tiktok_collector

# Test
test:
	docker compose exec api pytest -v

lint:
	docker compose exec api ruff check app/

# Frontend
fe-shell:
	docker compose exec frontend sh

fe-install:
	docker compose exec frontend npm install
