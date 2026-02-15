# Set up the project and install dependencies
setup:
    uv sync --frozen

# Run ruff linter
lint:
    uv run ruff check .

# Run ruff linter with auto-fix
fix-lint:
    uv run ruff check --fix .

# Run pytest tests
test:
    uv run pytest tests/

# Run the FastAPI development server
api:
    uv run uvicorn src.entrypoints.api:app --host 0.0.0.0 --port 8000 --reload

# Run the Celery worker
worker:
    uv run celery -A src.entrypoints.celery_worker worker --loglevel=info

# Run the Celery beat scheduler
beat:
    uv run celery -A src.entrypoints.celery_worker beat --loglevel=info

# Run Alembic migrations to head
migrate:
    uv run alembic upgrade head

# Create a new Alembic migration (usage: just migration "description")
migration message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Run all services in development mode
docker-dev:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Run all services in production mode
docker-prod:
    docker compose up --build

# Tear down all services and remove volumes
docker-down:
    docker compose down -v
