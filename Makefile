start-vk:
	uv run -m scripts.vk_comments_monitor
start-ya_maps:
	uv run -m scripts.ya_maps_reviews_monitor
cron-vk_monitor:
	/home/toro/.local/bin/uv run -m scripts.vk_comments_monitor
cron-ya_maps:
	/home/toro/.local/bin/uv run -m scripts.ya_maps_reviews_monitor

