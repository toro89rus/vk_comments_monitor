UV := $(shell which uv)

start-vk:
	$(UV) run -m scripts.vk_comments_monitor
start-ya_maps:
	$(UV) run -m scripts.ya_maps_reviews_monitor
cron-vk_monitor:
	$(UV) run -m scripts.vk_comments_monitor
cron-ya_maps:
	$(UV) run -m scripts.ya_maps_reviews_monitor
test:
	$(UV) run ruff check

install:
	uv sync

run:
	uv run -m tatd_bot.bot

