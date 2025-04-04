import json

import src.vk_comments_parser as vk_comments_parser
from config.settings import LATEST_VK_COMMENTS_FILE_PATH
from src.logger import logger
from src.tg import send_vk_comments

logger = logger.getChild("vk_comments")

logger.info("SCRIPT STARTED")
with open(LATEST_VK_COMMENTS_FILE_PATH, "r") as file:
    try:
        latest_vk_comments = json.load(file)
        logger.info("Latest comments loaded")
    except json.decoder.JSONDecodeError:
        logger.info("Latest comments file is empty")
        latest_vk_comments = {}


new_vk_comments = vk_comments_parser.get_new_comments(latest_vk_comments)
if new_vk_comments:
    logger.info("New comments found")
    send_vk_comments(new_vk_comments)
    logger.info("New comments sent")
    updated_latest_comments = vk_comments_parser.update_latest_comments(
        latest_vk_comments, new_vk_comments
    )
    logger.info("Latest comments updated")

    with open(LATEST_VK_COMMENTS_FILE_PATH, "w") as file:
        json.dump(updated_latest_comments, file)
        logger.info("Latest comments saved")
else:
    logger.info("No new comments found")
logger.info("SCRIPT ENDED")
