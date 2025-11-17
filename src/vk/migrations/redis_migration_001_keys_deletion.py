import src.cache as cache
from src.logger import logger

logger = logger.getChild(__name__)


def main():
    logger.info("Started migration")
    keys = cache.r.keys()

    for key in keys:
        if key.endswith("thread_comment"):
            logger.info(f"Deleting {key}")
            cache.r.delete(key)

    cache.r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
