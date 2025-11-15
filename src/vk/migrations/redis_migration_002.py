import src.cache as cache
from src.logger import logger

logger = logger.getChild(__name__)


def main():
    logger.info("Started migration")
    keys = cache.r.keys()

    for key in keys:
        if key.startswith("user"):
            cache.r.delete(key)

    cache.r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
