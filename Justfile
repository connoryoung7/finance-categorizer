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
