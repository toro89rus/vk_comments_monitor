from src.logger import logger
from src.cache import r, save_thread_comment_id
import re
logger = logger.getChild(__name__)


def main():

    keys = r.keys()
    for key in keys:
        post_id = re.search(r"\d+", key).group()
        value = r.get(f"post:{post_id}:last_comment") or r.get(
            f"post:{post_id}:last_comment_id"
        )
        comment_id = int(value  )
        save_thread_comment_id(post_id, comment_id, 0)

    r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
