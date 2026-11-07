from unittest.mock import patch

import pytest

from tatd_bot.config.config import (
    DATE_FORMAT,
    DATETIME_FORMAT,
    LOG_FORMAT,
    VkConfig,
    load_config,
)

ENV_VARS = (
    "TG_TOKEN",
    "ADMIN_ID",
    "VK_TOKEN",
    "VK_GROUP_ID",
    "VK_GROUP_NAME",
    "VK_MONITOR_UPDATE_DELAY",
    "REDIS",
    "ENV",
)


@pytest.fixture
def env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    with patch("tatd_bot.config.config.load_dotenv") as load_dotenv:
        yield monkeypatch, load_dotenv


def test_defaults(env):
    config = load_config()

    assert config.vk.token == ""
    assert config.vk.group_id == "-48164678"
    assert config.vk.group_name == "tuldramteatr"
    assert config.vk.update_delay == 300
    assert config.tg.token == ""
    assert config.tg.admin_id == 0
    assert config.redis.host == "localhost"
    assert config.env == "PROD"
    assert config.date_format == DATE_FORMAT
    assert config.datetime_format == DATETIME_FORMAT
    assert config.log_format == LOG_FORMAT


def test_values_from_environment(env):
    monkeypatch, _ = env
    monkeypatch.setenv("TG_TOKEN", "tg-token")
    monkeypatch.setenv("ADMIN_ID", "42")
    monkeypatch.setenv("VK_TOKEN", "vk-token")
    monkeypatch.setenv("VK_GROUP_ID", "-1")
    monkeypatch.setenv("VK_GROUP_NAME", "group")
    monkeypatch.setenv("VK_MONITOR_UPDATE_DELAY", "60")
    monkeypatch.setenv("REDIS", "redis")
    monkeypatch.setenv("ENV", "DEV")

    config = load_config()

    assert config.tg.token == "tg-token"
    assert config.tg.admin_id == 42
    assert config.vk.token == "vk-token"
    assert config.vk.group_id == "-1"
    assert config.vk.group_name == "group"
    assert config.vk.update_delay == 60
    assert config.redis.host == "redis"
    assert config.env == "DEV"


def test_dotenv_is_loaded_before_reading_environment(env):
    monkeypatch, load_dotenv = env
    load_dotenv.side_effect = lambda: monkeypatch.setenv("ADMIN_ID", "7")

    config = load_config()

    load_dotenv.assert_called_once_with()
    assert config.tg.admin_id == 7


@pytest.mark.parametrize("name", ["ADMIN_ID", "VK_MONITOR_UPDATE_DELAY"])
def test_non_integer_value_raises(env, name):
    monkeypatch, _ = env
    monkeypatch.setenv(name, "abc")

    with pytest.raises(ValueError):
        load_config()


def test_group_link():
    vk = VkConfig(token="", group_id="-1", group_name="group")

    assert vk.group_link == "https://vk.com/group?w=wall-1"
