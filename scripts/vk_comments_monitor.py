import json

import src.vk_comments_parser as vk_comments_parser
from config.settings import LATEST_VK_COMMENTS_FILE_PATH
from src.logger import logger
from src.tg import send_vk_comments

logger = logger.getChild("vk_comments")

logger.info("SCRIPT STARTED")

new_vk_comments = vk_comments_parser.get_new_comments()
if new_vk_comments:
    logger.info("New comments found")
    send_vk_comments(new_vk_comments)
    logger.info("New comments sent")
else:
    logger.info("No new comments found")
logger.info("SCRIPT ENDED")
