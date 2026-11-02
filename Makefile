.PHONY: setup eval test lint

setup:
	uv sync

eval:
	uv run python -m visit_scribe.evaluation

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
