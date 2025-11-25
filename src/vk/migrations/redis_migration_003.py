import redis

from src.logger import logger

logger = logger.getChild(__name__)


r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def main():
    logger.info("Started migration")
    keys = r.keys("comment:*")
    comments = {}
    for key in keys:
        comment_id = key.split(":")[1]
        comments.setdefault(comment_id, {})
        if not key.endswith("latest_reply"):
            logger.info(f"setting temp is_processed for {comment_id}")
            comments[comment_id]["is_processed"] = 1
            r.delete(key)

        else:
            logger.info(f"setting temp last_reply_id for {comment_id}")
            reply_id = r.get(key)
            comments[comment_id]["last_reply"] = reply_id
            r.delete(key)

    for comment_id in comments:
        new_key = f"comment:{comment_id}"
        logger.info(f"setting {comment_id} in repository")
        r.hset(new_key, mapping=comments[comment_id])
        r.expire(new_key, 604800)

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
