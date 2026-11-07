import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import SendMessage

from tatd_bot.monitor import VkCommentsMonitorService
from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.tg.models import BotUser, BotUserStatus
from tatd_bot.vk.models import Comment, Post, Reply, User
from tests.tg.fakes import FakeBot

CREATED_AT = datetime(2026, 3, 5, 9, 7)


def bot_user(user_id: int, status=BotUserStatus.NEW) -> BotUser:
    return BotUser(user_id, f"Пользователь {user_id}", f"user{user_id}", status)


class FakeFeedService:
    def __init__(self, posts: list[Post] | None = None):
        self.posts = posts or []
        self.saved: list[list[Post]] = []
        self.error: Exception | None = None

    async def get_new_comments(self) -> list[Post]:
        if self.error:
            raise self.error
        return self.posts

    async def save_comments_cache(self, posts: list[Post]) -> None:
        self.saved.append(posts)


def make_post() -> Post:
    author = User(1, "Иван", "Петров", "male")
    reply = Reply(11, CREATED_AT, User(2), "Ответ 11", author)
    comments = [
        Comment(10, CREATED_AT, author, "Комментарий 10", [reply], True),
        Comment(12, CREATED_AT, author, "Комментарий 12", [], True),
    ]
    return Post(1, CREATED_AT, "Пост", comments)


class StopMonitor(BaseException):
    """Прерывает бесконечный цикл monitor() на первом sleep."""


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def feed_service():
    return FakeFeedService([make_post()])


@pytest.fixture
def monitor_service(app_config, tg_repo, bot, feed_service):
    return VkCommentsMonitorService(
        config=app_config,
        repo=tg_repo,
        bot=bot,
        formatter=TgMessageFormatter(app_config),
        feed_service=feed_service,
    )


async def run_one_pass(monitor_service) -> None:
    with patch(
        "tatd_bot.monitor.asyncio.sleep",
        side_effect=StopMonitor,
    ):
        with pytest.raises(StopMonitor):
            await monitor_service.monitor()


class TestMonitor:
    async def test_sends_post_comments_and_replies_in_order(
        self, monitor_service, tg_repo, bot
    ):
        await tg_repo.add_subscriber(1)

        await run_one_pass(monitor_service)

        texts = bot.texts_for(1)
        assert len(texts) == 4
        assert texts[0].endswith("\nПост...")
        assert texts[1].endswith("\n\nКомментарий 10")
        assert texts[2].endswith("\n\nОтвет 11")
        assert texts[3].endswith("\n\nКомментарий 12")

    async def test_only_post_is_sent_as_html(
        self, monitor_service, tg_repo, bot
    ):
        await tg_repo.add_subscriber(1)

        await run_one_pass(monitor_service)

        # текущее поведение: комментарии и ответы — без parse_mode
        assert [m.parse_mode for m in bot.sent] == ["html", None, None, None]

    async def test_sends_to_every_subscriber_and_saves_cache(
        self, monitor_service, tg_repo, bot, feed_service
    ):
        await tg_repo.add_subscriber(1)
        await tg_repo.add_subscriber(2)

        await run_one_pass(monitor_service)

        assert len(bot.texts_for(1)) == 4
        assert len(bot.texts_for(2)) == 4
        assert feed_service.saved == [feed_service.posts]

    async def test_waits_update_delay_between_passes(
        self, monitor_service, app_config
    ):
        with patch(
            "tatd_bot.monitor.asyncio.sleep",
            side_effect=StopMonitor,
        ) as sleep:
            with pytest.raises(StopMonitor):
                await monitor_service.monitor()

        sleep.assert_called_once_with(app_config.vk.update_delay)

    async def test_nothing_new(
        self, monitor_service, tg_repo, bot, feed_service
    ):
        await tg_repo.add_subscriber(1)
        feed_service.posts = []

        await run_one_pass(monitor_service)

        assert bot.sent == []
        assert feed_service.saved == []

    async def test_no_subscribers_still_saves_cache(
        self, monitor_service, bot, feed_service
    ):
        await run_one_pass(monitor_service)

        assert bot.sent == []
        assert feed_service.saved == [feed_service.posts]

    async def test_blocked_subscriber_is_unsubscribed(
        self, monitor_service, tg_repo, bot, feed_service
    ):
        for user_id in (1, 2):
            await tg_repo.add_subscriber(user_id)
            await tg_repo.save_bot_user_info(
                bot_user(user_id, BotUserStatus.SUBSCRIBED)
            )
        bot.blocked_by = {1}

        await run_one_pass(monitor_service)

        assert await tg_repo.get_subscribers() == [2]
        assert (
            await tg_repo.get_bot_user(1)
        ).status is BotUserStatus.UNSUBSCRIBED
        assert len(bot.texts_for(2)) == 4
        assert feed_service.saved == [feed_service.posts]

    async def test_other_telegram_error_aborts_pass_without_saving(
        self, monitor_service, tg_repo, bot, feed_service
    ):
        await tg_repo.add_subscriber(1)
        await tg_repo.add_subscriber(2)
        bot.errors = {
            1: TelegramRetryAfter(
                method=SendMessage(chat_id=1, text=""),
                message="Too Many Requests",
                retry_after=5,
            )
        }

        await run_one_pass(monitor_service)

        # текущее поведение: подписчик 2 всё получил, но состояние не
        # сохранено, и на следующем проходе он получит то же самое
        assert len(bot.texts_for(2)) == 4
        assert feed_service.saved == []

    async def test_feed_error_does_not_stop_monitor(
        self, monitor_service, bot, feed_service
    ):
        feed_service.error = RuntimeError("VK недоступен")

        await run_one_pass(monitor_service)

        assert bot.sent == []

    async def test_cancellation_stops_monitor(self, monitor_service):
        with patch(
            "tatd_bot.monitor.asyncio.sleep",
            side_effect=asyncio.CancelledError,
        ):
            with pytest.raises(asyncio.CancelledError):
                await monitor_service.monitor()
