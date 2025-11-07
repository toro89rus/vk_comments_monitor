from src.logger import logger
from src.cache import r, save_thread_comment_id
import re
logger = logger.getChild(__name__)


def main():

    keys = r.keys()
    for key in keys:
        if "last_comment" in key:
            r.delete(key)

    r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
