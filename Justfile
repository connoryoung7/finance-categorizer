# Set up the project and install dependencies
setup:
    uv sync --frozen

# Run ruff linter
lint:
    uv run ruff check .

# Run ruff linter with auto-fix
fix-lint:
    uv run ruff check --fix .

# Lint the Dockerfile with pinned hadolint and the repo config
lint-dockerfile:
    docker run --rm \
        -v "$PWD/Dockerfile:/workspace/Dockerfile:ro" \
        -v "$PWD/.hadolint.yaml:/.config/hadolint.yaml:ro" \
        ghcr.io/hadolint/hadolint:v2.14.0 /workspace/Dockerfile

# Run all linters (Python + Dockerfile)
lint-all:
    just lint
    just lint-dockerfile

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

# Perform a security scan on the Docker image using Trivy
security-scan:
    docker build --target prod -t finance-categorizer .
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v trivy-cache:/root/.cache/ \
    -v "$PWD":/report \
    aquasec/trivy:latest image \
    --format sarif \
    --output /report/trivy-image-report.sarif \
    --detection-priority comprehensive \
    --severity CRITICAL finance-categorizer
