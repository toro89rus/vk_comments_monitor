import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from tatd_bot.config import AppConfig
from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.tg.models import BotUserStatus
from tatd_bot.tg.repository import TgRepository
from tatd_bot.vk.models import Post
from tatd_bot.vk.services import VkFeedService

logger = logging.getLogger(__name__)


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

    async def monitor(self):
        while True:
            try:
                logger.info("Started comments monitoring")
                new_vk_comments = self.feed_service.get_new_comments()
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
                    self.feed_service.save_comments_cache(new_vk_comments)
                    logger.info("New comments sent")
                else:
                    logger.info("No new comments found")
                logger.info("Finished comments monitoring")
            except Exception:
                logger.exception("Error during comments monitoring")
            await asyncio.sleep(self.config.vk.update_delay)

    async def _notify_subscribers(self, comments: list[Post]):
        subscribers_ids = self.repo.get_subscribers()
        tasks = (
            self._send_to_subscriber(subscriber_id, comments)
            for subscriber_id in subscribers_ids
        )
        await asyncio.gather(*tasks)
        logger.info(f"New comments sent to {len(subscribers_ids)}")

    async def _send_to_subscriber(
        self, subscriber_id: int, comments: list[Post]
    ):
        try:
            for post in comments:
                await self.bot.send_message(
                    subscriber_id,
                    self.formatter.format_post(post),
                    parse_mode="html",
                )

                for comment in post.comments:
                    await self.bot.send_message(
                        subscriber_id, self.formatter.format_comment(comment)
                    )
                    for reply in comment.replies:
                        await self.bot.send_message(
                            subscriber_id, self.formatter.format_reply(reply)
                        )
        except TelegramForbiddenError:
            logger.warning(
                "User %s blocked the bot. Removing from subscribers.",
                subscriber_id,
            )
            self.repo.remove_subscriber(subscriber_id)
            self.repo.set_bot_user_status(
                subscriber_id, BotUserStatus.UNSUBSCRIBED.value
            )
