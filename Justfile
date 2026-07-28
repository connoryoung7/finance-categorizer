# Set up the project and install dependencies
setup:
    uv sync --frozen

# Run ruff linter
lint:
    uv run ruff check .

# Run ruff linter with auto-fix
fix-lint:
    uv run ruff check --fix .

# Lint every Dockerfile in the project with pinned hadolint and the repo config
lint-dockerfile:
    #!/usr/bin/env bash
    set -euo pipefail
    files=$(git ls-files '*Dockerfile' '*Dockerfile.*' '*.dockerfile')
    if [ -z "$files" ]; then echo "No Dockerfiles found"; exit 0; fi
    echo "Linting:" $files
    docker run --rm \
        -v "$PWD:/workspace:ro" \
        -w /workspace \
        ghcr.io/hadolint/hadolint:v2.14.0 \
        --config /workspace/.hadolint.yaml $files

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
