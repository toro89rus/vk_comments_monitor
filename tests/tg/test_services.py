from unittest.mock import patch

import pytest

from tatd_bot.tg.models import BotUser, BotUserStatus
from tatd_bot.tg.services import (
    BotUserService,
    CreateSubRequestResult,
    TgSubscriptionService,
    UnsubscribeResult,
)


def bot_user(user_id: int, status=BotUserStatus.NEW) -> BotUser:
    return BotUser(user_id, f"Пользователь {user_id}", f"user{user_id}", status)


@pytest.fixture
def subscription_service(app_config, tg_repo):
    return TgSubscriptionService(app_config, tg_repo)


class TestRequestSubscription:
    async def test_creates_request(self, subscription_service, tg_repo):
        user = bot_user(1)

        result = await subscription_service.request_subscription(user)

        assert result is CreateSubRequestResult.REQUEST_CREATED
        assert await tg_repo.is_pending_subscriber(1) is True
        assert (await tg_repo.get_bot_user(1)).status is BotUserStatus.PENDING
        assert user.status is BotUserStatus.PENDING

    async def test_already_pending(self, subscription_service):
        await subscription_service.request_subscription(bot_user(1))

        result = await subscription_service.request_subscription(bot_user(1))

        assert result is CreateSubRequestResult.ALREADY_PENDING

    async def test_already_subscribed(self, subscription_service, tg_repo):
        await tg_repo.add_subscriber(1)

        result = await subscription_service.request_subscription(bot_user(1))

        assert result is CreateSubRequestResult.ALREADY_SUBBED
        assert await tg_repo.is_pending_subscriber(1) is False

    async def test_rejected_user_can_request_again(
        self, subscription_service, tg_repo
    ):
        await subscription_service.request_subscription(bot_user(1))
        await subscription_service.decline_subscriber(1)

        result = await subscription_service.request_subscription(
            await tg_repo.get_bot_user(1)
        )

        assert result is CreateSubRequestResult.REQUEST_CREATED


class TestUnsubscribe:
    async def test_unsubscribes_subscriber(self, subscription_service, tg_repo):
        await tg_repo.add_subscriber(1)
        user = bot_user(1, BotUserStatus.SUBSCRIBED)

        result = await subscription_service.unsubscribe(user)

        assert result is UnsubscribeResult.UNSUBSCRIBED
        assert await tg_repo.is_subscriber(1) is False
        assert (
            await tg_repo.get_bot_user(1)
        ).status is BotUserStatus.UNSUBSCRIBED

    async def test_not_subscribed(self, subscription_service, tg_repo):
        result = await subscription_service.unsubscribe(bot_user(1))

        assert result is UnsubscribeResult.NOT_SUBSCRIBED
        assert await tg_repo.get_bot_user(1) is None

    async def test_pending_user_is_not_subscribed(
        self, subscription_service, tg_repo
    ):
        await subscription_service.request_subscription(bot_user(1))

        result = await subscription_service.unsubscribe(bot_user(1))

        # текущее поведение: заявка остаётся в очереди
        assert result is UnsubscribeResult.NOT_SUBSCRIBED
        assert await tg_repo.is_pending_subscriber(1) is True


class TestReviewApplications:
    async def test_pending_application_user_is_the_oldest(
        self, subscription_service
    ):
        with patch("tatd_bot.tg.repository.time") as fake_time:
            fake_time.time.side_effect = [20, 10]
            await subscription_service.request_subscription(bot_user(2))
            await subscription_service.request_subscription(bot_user(1))

        assert await subscription_service.get_pending_subscribers() == [1, 2]
        assert await subscription_service.get_pending_application_user() == (
            bot_user(1, BotUserStatus.PENDING)
        )

    async def test_no_pending_application(self, subscription_service):
        assert await subscription_service.get_pending_application_user() is None

    async def test_accept(self, subscription_service, tg_repo):
        await subscription_service.request_subscription(bot_user(1))

        await subscription_service.accept_subscriber(1)

        assert await tg_repo.is_subscriber(1) is True
        assert await tg_repo.is_pending_subscriber(1) is False
        assert (
            await tg_repo.get_bot_user(1)
        ).status is BotUserStatus.SUBSCRIBED

    async def test_decline(self, subscription_service, tg_repo):
        await subscription_service.request_subscription(bot_user(1))

        await subscription_service.decline_subscriber(1)

        assert await tg_repo.is_subscriber(1) is False
        assert await tg_repo.is_pending_subscriber(1) is False
        assert (await tg_repo.get_bot_user(1)).status is BotUserStatus.REJECTED


class TestBotUserService:
    async def test_save_and_get_user(self, tg_repo):
        service = BotUserService(tg_repo)

        result = await service.save_user_info(bot_user(1))

        assert await service.get_user(1) == bot_user(1)
        assert result is None
