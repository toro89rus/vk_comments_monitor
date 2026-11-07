import asyncio
import logging
from collections.abc import Iterator

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from tatd_bot.config import AppConfig
from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.tg.models import BotUserStatus
from tatd_bot.tg.repository import TgRepository
from tatd_bot.vk.models import Post
from tatd_bot.vk.services import VkFeedService

logger = logging.getLogger(__name__)

# Сколько подписчикам рассылать одновременно
MAX_CONCURRENT_SENDS = 5
# Сколько раз повторять сообщение после TelegramRetryAfter
MAX_SEND_RETRIES = 3


class VkCommentsMonitorService:
    def __init__(
        self,
        config: AppConfig,
        repo: TgRepository,
        bot: Bot,
        formatter: TgMessageFormatter,
        feed_service: VkFeedService,
    ):
        self.config = config
        self.repo = repo
        self.bot = bot
        self.formatter = formatter
        self.feed_service = feed_service
        self._send_limit = asyncio.Semaphore(MAX_CONCURRENT_SENDS)

    async def monitor(self):
        while True:
            try:
                logger.info("Started comments monitoring")
                new_vk_comments = await self.feed_service.get_new_comments()
                if new_vk_comments:
                    total_comments = sum(
                        len(post.comments) for post in new_vk_comments
                    )
                    logger.info(
                        "Collected %s posts with %s comments",
                        len(new_vk_comments),
                        total_comments,
                    )
                    await self._notify_subscribers(new_vk_comments)
                    await self.feed_service.save_comments_cache(new_vk_comments)
                    logger.info("New comments sent")
                else:
                    logger.info("No new comments found")
                logger.info("Finished comments monitoring")
            except Exception:
                logger.exception("Error during comments monitoring")
            await asyncio.sleep(self.config.vk.update_delay)

    async def _notify_subscribers(self, comments: list[Post]):
        subscribers_ids = await self.repo.get_subscribers()
        tasks = (
            self._send_to_subscriber(subscriber_id, comments)
            for subscriber_id in subscribers_ids
        )
        await asyncio.gather(*tasks)
        logger.info(f"New comments sent to {len(subscribers_ids)}")

    async def _send_to_subscriber(
        self, subscriber_id: int, comments: list[Post]
    ) -> None:
        async with self._send_limit:
            try:
                for text, parse_mode in self._messages(comments):
                    await self._send_with_retry(subscriber_id, text, parse_mode)
            except TelegramForbiddenError:
                logger.warning(
                    "User %s blocked the bot. Removing from subscribers.",
                    subscriber_id,
                )
                await self.repo.remove_subscriber(subscriber_id)
                await self.repo.set_bot_user_status(
                    subscriber_id, BotUserStatus.UNSUBSCRIBED.value
                )
            except TelegramAPIError:
                # Остальные подписчики не страдают: проход продолжается, и
                # состояние сохраняется, чтобы не повторять рассылку всем
                logger.exception(
                    "Failed to send new comments to user %s", subscriber_id
                )

    def _messages(
        self, comments: list[Post]
    ) -> Iterator[tuple[str, str | None]]:
        for post in comments:
            yield self.formatter.format_post(post), "html"
            for comment in post.comments:
                yield self.formatter.format_comment(comment), None
                for reply in comment.replies:
                    yield self.formatter.format_reply(reply), None

    async def _send_with_retry(
        self, chat_id: int, text: str, parse_mode: str | None
    ) -> None:
        for attempt in range(MAX_SEND_RETRIES):
            try:
                await self.bot.send_message(
                    chat_id, text, parse_mode=parse_mode
                )
                return
            except TelegramRetryAfter as e:
                logger.warning(
                    "Flood control for user %s, retry %s in %s s",
                    chat_id,
                    attempt + 1,
                    e.retry_after,
                )
                await asyncio.sleep(e.retry_after)
        await self.bot.send_message(chat_id, text, parse_mode=parse_mode)
