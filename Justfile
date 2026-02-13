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
