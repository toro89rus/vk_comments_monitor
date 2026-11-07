from unittest.mock import patch

import pytest
from petrovich.enums import Gender

from tatd_bot.config.config import RedisConfig
from tatd_bot.repository import COMMENT_TTL, USER_TTL, create_redis_client
from tatd_bot.tg.models import BotUser, BotUserStatus

DAY = 24 * 60 * 60


def test_create_redis_client_settings():
    client = create_redis_client(RedisConfig(host="redis", port=6380))

    kwargs = client.connection_pool.connection_kwargs
    assert kwargs["host"] == "redis"
    assert kwargs["port"] == 6380
    assert kwargs["decode_responses"] is True


def test_ttl_values():
    assert USER_TTL == 30 * DAY
    assert COMMENT_TTL == 8 * DAY


class TestVkUser:
    def test_save_and_get_user(self, repo, redis_client):
        repo.save_user(1, "Иван", "Петров", Gender.MALE)

        assert repo.get_user(1) == {
            "first_name": "Иван",
            "last_name": "Петров",
            "gender": "male",
        }
        assert redis_client.ttl("user:1") == USER_TTL

    def test_get_missing_user_returns_empty_dict(self, repo):
        assert repo.get_user(1) == {}

    def test_save_user_overwrites_fields(self, repo):
        repo.save_user(1, "Иван", "Петров", "male")
        repo.save_user(1, "Пётр", "", "")

        assert repo.get_user(1) == {
            "first_name": "Пётр",
            "last_name": "",
            "gender": "",
        }


class TestVkGroup:
    def test_save_and_get_group_name(self, repo, redis_client):
        repo.save_group_name(5, "Театр")

        assert repo.get_group_name(5) == "Театр"
        assert redis_client.hgetall("group:5:name") == {"name": "Театр"}
        assert redis_client.ttl("group:5:name") == USER_TTL

    def test_get_missing_group_name(self, repo):
        assert repo.get_group_name(5) is None


class TestComment:
    def test_new_comment_is_not_processed(self, repo):
        assert repo.is_comment_processed(1) is False

    def test_process_comment(self, repo, redis_client):
        repo.process_comment(1)

        assert repo.is_comment_processed(1) is True
        assert redis_client.hgetall("comment:1") == {"is_processed": "1"}
        assert redis_client.ttl("comment:1") == COMMENT_TTL

    def test_last_reply_id(self, repo, redis_client):
        assert repo.get_last_reply_id(1) is None

        repo.save_last_reply_id(1, 77)

        assert repo.get_last_reply_id(1) == 77
        assert redis_client.ttl("comment:1") == COMMENT_TTL

    def test_last_reply_id_does_not_mark_comment_processed(self, repo):
        repo.save_last_reply_id(1, 77)

        assert repo.is_comment_processed(1) is False

    def test_process_and_last_reply_share_one_hash(self, repo, redis_client):
        repo.process_comment(1)
        repo.save_last_reply_id(1, 77)

        assert redis_client.hgetall("comment:1") == {
            "is_processed": "1",
            "last_reply_id": "77",
        }

    def test_saving_reply_refreshes_ttl(self, repo, redis_client):
        repo.process_comment(1)
        redis_client.expire("comment:1", 10)

        repo.save_last_reply_id(1, 77)

        assert redis_client.ttl("comment:1") == COMMENT_TTL


class TestSubscribers:
    def test_add_and_remove_subscriber(self, repo, redis_client):
        repo.add_subscriber(1)

        assert repo.is_subscriber(1) is True
        assert redis_client.smembers("subscribers") == {"1"}

        repo.remove_subscriber(1)

        assert repo.is_subscriber(1) is False

    def test_get_subscribers_returns_ints(self, repo):
        repo.add_subscriber(1)
        repo.add_subscriber(2)
        repo.add_subscriber(2)

        assert sorted(repo.get_subscribers()) == [1, 2]

    def test_subscribers_have_no_ttl(self, repo, redis_client):
        repo.add_subscriber(1)

        assert redis_client.ttl("subscribers") == -1


class TestPendingSubscribers:
    def test_add_and_remove_pending_subscriber(self, repo):
        repo.add_pending_subscriber(1)

        assert repo.is_pending_subscriber(1) is True

        repo.remove_pending_subscriber(1)

        assert repo.is_pending_subscriber(1) is False

    def test_pending_subscribers_are_ordered_by_request_time(self, repo):
        with patch("tatd_bot.repository.time") as fake_time:
            fake_time.time.side_effect = [30, 10, 20]
            repo.add_pending_subscriber(3)
            repo.add_pending_subscriber(1)
            repo.add_pending_subscriber(2)

        assert repo.get_pending_subscribers() == [1, 2, 3]
        assert repo.get_pending_subscriber() == 1

    def test_no_pending_subscribers(self, repo):
        assert repo.get_pending_subscribers() == []
        assert repo.get_pending_subscriber() is None

    def test_repeated_request_updates_its_time(self, repo):
        with patch("tatd_bot.repository.time") as fake_time:
            fake_time.time.side_effect = [10, 20, 30]
            repo.add_pending_subscriber(1)
            repo.add_pending_subscriber(2)
            repo.add_pending_subscriber(1)

        assert repo.get_pending_subscribers() == [2, 1]


class TestBotUser:
    def test_save_and_get_bot_user(self, repo, redis_client):
        user = BotUser(1, "Иван Петров", "ivan", BotUserStatus.PENDING)

        repo.save_bot_user_info(user)

        assert repo.get_bot_user(1) == user
        assert redis_client.hgetall("bot_user:1") == {
            "full_name": "Иван Петров",
            "username": "ivan",
            "status": "pending",
        }
        assert redis_client.ttl("bot_user:1") == -1

    def test_get_missing_bot_user(self, repo):
        assert repo.get_bot_user(1) is None

    def test_set_bot_user_status(self, repo):
        repo.save_bot_user_info(BotUser(1, "Иван", None, BotUserStatus.NEW))

        repo.set_bot_user_status(1, BotUserStatus.SUBSCRIBED.value)

        assert repo.get_bot_user(1).status is BotUserStatus.SUBSCRIBED

    def test_set_status_of_missing_user_does_nothing(self, repo, redis_client):
        repo.set_bot_user_status(1, BotUserStatus.SUBSCRIBED.value)

        assert redis_client.exists("bot_user:1") == 0

    def test_get_bot_user_with_unknown_status_raises(self, repo, redis_client):
        redis_client.hset(
            "bot_user:1",
            mapping={"full_name": "Иван", "username": "", "status": "bogus"},
        )

        with pytest.raises(ValueError, match="bogus"):
            repo.get_bot_user(1)
