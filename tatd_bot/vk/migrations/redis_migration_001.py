import tatd_bot.repository as repository
from tatd_bot.logger import logger

logger = logger.getChild(__name__)


def main():
    logger.info("Started migration")
    keys = repository.r.keys()

    for key in keys:
        if key.startswith("post"):
            comment_id = int(key.split(":")[3])
            reply_id = int(repository.r.get(key))
            if reply_id == 0:
                repository.proccess_comment(comment_id)
            else:
                repository.save_last_reply_id(comment_id, reply_id)

    repository.r.close()
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
