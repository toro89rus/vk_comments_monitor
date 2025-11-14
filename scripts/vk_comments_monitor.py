import src.vk.comments_parser as vk_comments_parser
from src import cache
from src.logger import logger
from src.tg import send_vk_comments

logger = logger.getChild("vk_comments")

logger.info("SCRIPT STARTED")

new_vk_comments = vk_comments_parser.get_new_comments()
if new_vk_comments:
    logger.info(f"Collected {len(new_vk_comments)} posts with new comments")
    send_vk_comments(new_vk_comments)
    for post in new_vk_comments:
        for comment in post.comments:
            if comment.is_new:
                cache.proccess_comment(comment.id)
            if comment.replies:
                cache.save_last_reply_id(comment.id, comment.replies[-1].id)
    logger.info("New comments sent")
else:
    logger.info("No new comments found")
logger.info("SCRIPT ENDED")
