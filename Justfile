# Run ruff linter
lint:
    uv run ruff check .

# Run ruff linter with auto-fix
fix-lint:
    uv run ruff check --fix .
