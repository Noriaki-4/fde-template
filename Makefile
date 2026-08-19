.PHONY: help install dev up down test lint format clean deploy destroy

help:
	@echo "FDE Template Commands"
	@echo "===================="
	@echo "make install      - Install dependencies"
	@echo "make dev          - Setup dev environment"
	@echo "make up           - Start containers (core services)"
	@echo "make up-search    - + OpenSearch"
	@echo "make up-graph     - + Neo4j + Virtuoso"
	@echo "make up-rdf       - + Virtuoso only"
	@echo "make up-nosql     - + ScyllaDB"
	@echo "make up-streamlit - + Streamlit UI"
	@echo "make up-mcp       - + Mock Business API + MCP server"
	@echo "make down         - Stop containers"
	@echo "make logs         - Tail service logs"
	@echo "make db-reset     - Drop and re-create database schema"
	@echo "make seed         - Seed sample data"
	@echo "make test         - Run tests"
	@echo "make coverage     - Test coverage report"
	@echo "make lint         - Lint code"
	@echo "make format       - Format code"
	@echo "make type-check   - Type checking"
	@echo "make clean        - Clean artifacts"
	@echo "make deploy       - Deploy to AWS"
	@echo "make destroy      - Destroy AWS stack"

install:
	uv venv
	uv pip install -e ".[dev]"
	cd cdk && npm install && cd ..

dev: install
	pre-commit install
	cp .env.example .env.local

up:
	docker compose -f infra/docker-compose.yml up -d
	@echo "✓ Services started"
	@echo "Frontend: http://localhost:7860"
	@echo "Backend: http://localhost:8000"

up-search:
	docker compose -f infra/docker-compose.yml --profile with-search up -d

up-graph:
	docker compose -f infra/docker-compose.yml --profile with-graph up -d

up-rdf:
	docker compose -f infra/docker-compose.yml --profile with-rdf up -d

up-nosql:
	docker compose -f infra/docker-compose.yml --profile with-nosql up -d

up-streamlit:
	docker compose -f infra/docker-compose.yml --profile with-streamlit up -d

up-mcp:
	docker compose -f infra/docker-compose.yml --profile with-mcp up -d

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

db-reset:
	uv run python scripts/init_db.py drop
	uv run python scripts/init_db.py

db-init:
	uv run python scripts/init_db.py

seed: db-init
	uv run python scripts/seed_documents.py
	uv run python scripts/seed_graph.py

backend:
	cd backend && uv run uvicorn api.main:app --reload

frontend:
	cd frontend/gradio && uv run python app.py

test:
	uv run pytest -v

test-unit:
	uv run pytest -v -m unit

test-integration:
	uv run pytest -v -m integration

coverage:
	uv run pytest --cov=backend --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run black .
	uv run ruff check --fix .

type-check:
	uv run mypy backend/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info

verify:
	@echo "Running verification checks..."
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test
	@echo "✓ All checks passed"

deploy:
	cd cdk && npm run deploy

diff:
	cd cdk && npm run diff

destroy:
	cd cdk && npm run destroy

.DEFAULT_GOAL := help
