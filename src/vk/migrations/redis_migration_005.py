import redis

from src.logger import logger

logger = logger.getChild(__name__)


r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def main():
    logger.info("Started migration")
    keys = r.keys("comment:*")
    for key in keys:
        old_ttl = r.ttl(key)
        r.expire(key, old_ttl + (24 * 60 * 60))

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
