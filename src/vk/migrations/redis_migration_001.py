import src.cache as cache
from src.logger import logger

logger = logger.getChild(__name__)


def main():
    logger.info("Started migration")
    keys = cache.r.keys()

    for key in keys:
        if key.startswith("post"):
            comment_id = int(key.split(":")[3])
            reply_id = int(cache.r.get(key))
            if reply_id == 0:
                cache.proccess_comment(comment_id)
            else:
                cache.save_last_reply_id(comment_id, reply_id)

    cache.r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
