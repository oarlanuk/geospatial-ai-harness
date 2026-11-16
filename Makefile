.PHONY: setup fix check format-check lint types

# One-time setup: install tools and the git hooks.
setup:
	uv sync
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# Rewrite files: format, then apply safe lint fixes.
fix:
	uv run ruff format .
	uv run ruff check --fix .

# Verify only, change nothing. CI runs exactly this.
check: format-check lint types

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

types:
	uv run python scripts/run_pyright.py
