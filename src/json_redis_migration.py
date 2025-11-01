import json
import redis
from pathlib import Path

from config.settings import LATEST_VK_COMMENTS_FILE_PATH
from src.logger import logger

logger = logger.getChild("migration")


def main():

    with open(LATEST_VK_COMMENTS_FILE_PATH, "r") as file:
        latest_vk_comments = json.load(file)

    logger.info(f"Loaded {len(latest_vk_comments)} records from JSON")

    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    for post_id in latest_vk_comments:
        try:
            comment_id = latest_vk_comments[post_id]["comment_id"]
            if not r.exists(post_id):
                r.set(post_id, comment_id, ex=604800)
                logger.info(f"Migrated post {post_id} → comment {comment_id}")
        except Exception as e:
            logger.error(f"Failed to migrate {post_id}: {e}")

    path = Path(LATEST_VK_COMMENTS_FILE_PATH)

    try:
        path.unlink()
        logger.info(f"Deleted JSON file: {path}")
    except Exception as e:
        logger.warning(f"Could not delete file {path}: {e}")

    r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
