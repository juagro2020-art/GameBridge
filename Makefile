.PHONY: help install run migrate test seed demo-reset lint docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make run          - Run FastAPI application locally"
	@echo "  make migrate      - Run Alembic database migrations"
	@echo "  make test         - Run full pytest test suite"
	@echo "  make seed         - Seed database with demonstration data"
	@echo "  make demo-reset   - Safely wipe and re-seed demo data"
	@echo "  make docker-up    - Start Docker Compose services"
	@echo "  make docker-down  - Stop Docker Compose services"

install:
	pip install -e .

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

test:
	pytest -v

seed:
	python -m scripts.seed_demo

demo-reset:
	python -m scripts.reset_demo

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
