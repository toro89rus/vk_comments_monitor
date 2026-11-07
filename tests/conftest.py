import fakeredis
import pytest

from tatd_bot.config.config import (
    DATE_FORMAT,
    DATETIME_FORMAT,
    LOG_FORMAT,
    AppConfig,
    RedisConfig,
    TgConfig,
    VkConfig,
)
from tatd_bot.tg.repository import TgRepository
from tatd_bot.vk.repository import VkRepository

ADMIN_ID = 1000


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(
        vk=VkConfig(token="vk-test-token"),
        tg=TgConfig(token="tg-test-token", admin_id=ADMIN_ID),
        redis=RedisConfig(host="localhost"),
        env="TEST",
        date_format=DATE_FORMAT,
        datetime_format=DATETIME_FORMAT,
        log_format=LOG_FORMAT,
    )


@pytest.fixture
def redis_client() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def tg_repo(redis_client) -> TgRepository:
    return TgRepository(redis_client)


@pytest.fixture
def vk_repo(redis_client) -> VkRepository:
    return VkRepository(redis_client)
