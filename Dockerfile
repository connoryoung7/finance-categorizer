FROM python:3.13.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl ca-certificates procps build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

ENV PATH="/app/.venv/bin:$PATH"

# --- prod ---
FROM base AS prod
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/

# --- dev ---
FROM base AS dev
RUN uv sync --frozen --no-install-project
# Source code is volume-mounted at runtime, not copied
||||||| Stash base

# --- prod ---
FROM gcr.io/distroless/python3-debian12:nonroot AS prod

WORKDIR /app

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONPATH="/app"

