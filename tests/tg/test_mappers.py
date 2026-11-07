import pytest
from aiogram.types import User

from tatd_bot.tg.mappers.mappers import (
    map_bot_user_to_redis,
    map_redis_to_bot_user,
    map_tg_to_bot_user,
)
from tatd_bot.tg.models.models import BotUser, BotUserStatus


def test_map_tg_to_bot_user_defaults_to_new_status():
    tg_user = User(
        id=1,
        is_bot=False,
        first_name="Иван",
        last_name="Петров",
        username="ivan",
    )

    assert map_tg_to_bot_user(tg_user) == BotUser(
        id=1,
        full_name="Иван Петров",
        username="ivan",
        status=BotUserStatus.NEW,
    )


def test_map_tg_to_bot_user_with_status():
    tg_user = User(id=1, is_bot=False, first_name="Иван")

    bot_user = map_tg_to_bot_user(tg_user, BotUserStatus.PENDING)

    assert bot_user.full_name == "Иван"
    assert bot_user.username is None
    assert bot_user.status is BotUserStatus.PENDING


def test_map_bot_user_to_redis_stores_missing_username_as_empty_string():
    bot_user = BotUser(1, "Иван", None, BotUserStatus.SUBSCRIBED)

    assert map_bot_user_to_redis(bot_user) == {
        "full_name": "Иван",
        "username": "",
        "status": "subscribed",
    }


@pytest.mark.parametrize("status", list(BotUserStatus))
def test_bot_user_redis_round_trip(status):
    bot_user = BotUser(1, "Иван", "ivan", status)

    data = map_bot_user_to_redis(bot_user)

    assert map_redis_to_bot_user(1, data) == bot_user


def test_redis_round_trip_turns_missing_username_into_empty_string():
    bot_user = BotUser(1, "Иван", None, BotUserStatus.NEW)

    data = map_bot_user_to_redis(bot_user)

    # текущее поведение: None после Redis становится ""
    assert map_redis_to_bot_user(1, data).username == ""
