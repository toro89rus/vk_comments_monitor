from unittest.mock import patch

import pytest

from tatd_bot.tg.models import BotUser, BotUserStatus


class TestSubscribers:
    async def test_add_and_remove_subscriber(self, tg_repo, redis_client):
        await tg_repo.add_subscriber(1)

        assert await tg_repo.is_subscriber(1) is True
        assert await redis_client.smembers("subscribers") == {"1"}

        await tg_repo.remove_subscriber(1)

        assert await tg_repo.is_subscriber(1) is False

    async def test_get_subscribers_returns_ints(self, tg_repo):
        await tg_repo.add_subscriber(1)
        await tg_repo.add_subscriber(2)
        await tg_repo.add_subscriber(2)

        assert sorted(await tg_repo.get_subscribers()) == [1, 2]

    async def test_subscribers_have_no_ttl(self, tg_repo, redis_client):
        await tg_repo.add_subscriber(1)

        assert await redis_client.ttl("subscribers") == -1


class TestPendingSubscribers:
    async def test_add_and_remove_pending_subscriber(self, tg_repo):
        await tg_repo.add_pending_subscriber(1)

        assert await tg_repo.is_pending_subscriber(1) is True

        await tg_repo.remove_pending_subscriber(1)

        assert await tg_repo.is_pending_subscriber(1) is False

    async def test_pending_subscribers_are_ordered_by_request_time(
        self, tg_repo
    ):
        with patch("tatd_bot.tg.repository.time") as fake_time:
            fake_time.time.side_effect = [30, 10, 20]
            await tg_repo.add_pending_subscriber(3)
            await tg_repo.add_pending_subscriber(1)
            await tg_repo.add_pending_subscriber(2)

        assert await tg_repo.get_pending_subscribers() == [1, 2, 3]
        assert await tg_repo.get_pending_subscriber() == 1

    async def test_no_pending_subscribers(self, tg_repo):
        assert await tg_repo.get_pending_subscribers() == []
        assert await tg_repo.get_pending_subscriber() is None

    async def test_repeated_request_updates_its_time(self, tg_repo):
        with patch("tatd_bot.tg.repository.time") as fake_time:
            fake_time.time.side_effect = [10, 20, 30]
            await tg_repo.add_pending_subscriber(1)
            await tg_repo.add_pending_subscriber(2)
            await tg_repo.add_pending_subscriber(1)

        assert await tg_repo.get_pending_subscribers() == [2, 1]


class TestBotUser:
    async def test_save_and_get_bot_user(self, tg_repo, redis_client):
        user = BotUser(1, "Иван Петров", "ivan", BotUserStatus.PENDING)

        await tg_repo.save_bot_user_info(user)

        assert await tg_repo.get_bot_user(1) == user
        assert await redis_client.hgetall("bot_user:1") == {
            "full_name": "Иван Петров",
            "username": "ivan",
            "status": "pending",
        }
        assert await redis_client.ttl("bot_user:1") == -1

    async def test_get_missing_bot_user(self, tg_repo):
        assert await tg_repo.get_bot_user(1) is None

    async def test_set_bot_user_status(self, tg_repo):
        await tg_repo.save_bot_user_info(
            BotUser(1, "Иван", None, BotUserStatus.NEW)
        )

        await tg_repo.set_bot_user_status(1, BotUserStatus.SUBSCRIBED.value)

        assert (
            await tg_repo.get_bot_user(1)
        ).status is BotUserStatus.SUBSCRIBED

    async def test_set_status_of_missing_user_does_nothing(
        self, tg_repo, redis_client
    ):
        await tg_repo.set_bot_user_status(1, BotUserStatus.SUBSCRIBED.value)

        assert await redis_client.exists("bot_user:1") == 0

    async def test_get_bot_user_with_unknown_status_raises(
        self, tg_repo, redis_client
    ):
        await redis_client.hset(
            "bot_user:1",
            mapping={"full_name": "Иван", "username": "", "status": "bogus"},
        )

        with pytest.raises(ValueError, match="bogus"):
            await tg_repo.get_bot_user(1)
