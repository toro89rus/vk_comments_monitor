from tatd_bot.logger import logger
from tatd_bot.tg import send_vk_comments
from tatd_bot.vk.comments_parser import get_new_comments
from tatd_bot.vk.services import update_comments_cache

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
