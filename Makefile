UV := $(shell which uv)

lint:
	$(UV) run ruff check
format:
	$(UV) run ruff format
test:
	$(UV) run pytest
check:
	$(UV) run ruff format --check
	$(UV) run ruff check
	$(UV) run pytest

install:
	uv sync

run:
	uv run --locked --no-dev -m tatd_bot.bot

