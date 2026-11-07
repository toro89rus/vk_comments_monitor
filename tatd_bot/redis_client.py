import redis

from tatd_bot.config.config import RedisConfig


def create_redis_client(config: RedisConfig) -> redis.Redis:
    return redis.Redis(
        host=config.host, port=config.port, decode_responses=True
    )
