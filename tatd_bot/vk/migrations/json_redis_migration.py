import json
import logging

from tatd_bot.config import load_config
from tatd_bot.repository import Repository

LATEST_VK_COMMENTS_FILE_PATH = "storage/latest_vk_comments.json"


def main():
    config = load_config()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("migration")

    repo = Repository(config.redis.host)
    r = repo.r

    try:
        with open(LATEST_VK_COMMENTS_FILE_PATH, "r") as file:
            latest_vk_comments = json.load(file)
    except FileNotFoundError:
        logger.warning(
            "File %s not found, nothing to migrate",
            LATEST_VK_COMMENTS_FILE_PATH,
        )
        return

    logger.info("Loaded %s records from JSON", len(latest_vk_comments))

    for post_id in latest_vk_comments:
        try:
            comment_id = latest_vk_comments[post_id]["comment_id"]
            r.set(f"post:{post_id}:last_comment", comment_id, ex=604800)
            logger.info("Migrated post %s → comment %s", post_id, comment_id)
        except Exception as e:
            logger.error("Failed to migrate %s: %s", post_id, e)

    r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
