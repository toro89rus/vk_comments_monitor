from tatd_bot.config.config import RedisConfig
from tatd_bot.redis_client import create_redis_client


def test_create_redis_client_settings():
    client = create_redis_client(RedisConfig(host="redis", port=6380))

    kwargs = client.connection_pool.connection_kwargs
    assert kwargs["host"] == "redis"
    assert kwargs["port"] == 6380
    assert kwargs["decode_responses"] is True
