import src.repository as repository
from src.logger import logger

logger = logger.getChild(__name__)


def main():
    logger.info("Started migration")
    keys = repository.r.keys()

    for key in keys:
        if key.endswith("thread_comment"):
            logger.info(f"Deleting {key}")
            repository.r.delete(key)

    repository.r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
