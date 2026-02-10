import redis

from tatd_bot.logger import logger

logger = logger.getChild(__name__)


r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def main():
    logger.info("Started migration")
    keys = r.keys("group:*")
    for key in keys:
        group_id = key.split(":")[1]
        group_name = r.get(key)
        new_key = f"group:{group_id}"
        r.hset(new_key, "name", group_name)
        r.expire(new_key, 2592000)
        r.delete(key)

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
