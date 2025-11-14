from src.vk.comments_parser import get_new_comments, update_comments_cache
from src.logger import logger
from src.tg import send_vk_comments

logger = logger.getChild("vk_comments")

logger.info("SCRIPT STARTED")

new_vk_comments = get_new_comments()
if new_vk_comments:
    logger.info(f"Collected {len(new_vk_comments)} posts with new comments")
    send_vk_comments(new_vk_comments)
    update_comments_cache(new_vk_comments)

    logger.info("New comments sent")
else:
    logger.info("No new comments found")
logger.info("SCRIPT ENDED")
