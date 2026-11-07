import asyncio
import logging
from enum import Enum

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from tatd_bot.config import AppConfig
from tatd_bot.repository import Repository
from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.tg.models.models import BotUser, BotUserStatus
from tatd_bot.vk.models import Post
from tatd_bot.vk.services import VkFeedService

logger = logging.getLogger(__name__)


class VkCommentsMonitorService:
    def __init__(
        self,
        config: AppConfig,
        repo: Repository,
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


class CreateSubRequestResult(Enum):
    ALREADY_SUBBED = "already_subscribed"
    ALREADY_PENDING = "already_pending"
    REQUEST_CREATED = "request_created"


class UnsubscribeResult(Enum):
    UNSUBSCRIBED = "unsubscribed"
    NOT_SUBSCRIBED = "not_subscribed"


class TgSubscriptionService:
    def __init__(self, config: AppConfig, repo: Repository):
        self.config = config
        self.repo = repo

    async def request_subscription(
        self, user: BotUser
    ) -> CreateSubRequestResult:
        if self.repo.is_subscriber(user.id):
            return CreateSubRequestResult.ALREADY_SUBBED
        if self.repo.is_pending_subscriber(user.id):
            return CreateSubRequestResult.ALREADY_PENDING
        user.status = BotUserStatus.PENDING
        self.repo.save_bot_user_info(user)
        self.repo.add_pending_subscriber(user.id)
        return CreateSubRequestResult.REQUEST_CREATED

    async def unsubscribe(self, user: BotUser) -> UnsubscribeResult:
        if self.repo.is_subscriber(user.id):
            self.repo.remove_subscriber(user.id)
            user.status = BotUserStatus.UNSUBSCRIBED
            self.repo.save_bot_user_info(user)
            return UnsubscribeResult.UNSUBSCRIBED

        else:
            return UnsubscribeResult.NOT_SUBSCRIBED

    def get_pending_subscribers(self):
        return self.repo.get_pending_subscribers()

    def get_pending_application_user(self) -> BotUser | None:
        user_id = self.repo.get_pending_subscriber()
        if user_id:
            return self.repo.get_bot_user(user_id)
        return None

    def accept_subscriber(self, user_id: int) -> None:
        self.repo.add_subscriber(user_id)
        self.repo.set_bot_user_status(user_id, BotUserStatus.SUBSCRIBED.value)
        self.repo.remove_pending_subscriber(user_id)

    def decline_subscriber(self, user_id: int) -> None:
        self.repo.set_bot_user_status(user_id, BotUserStatus.REJECTED.value)
        self.repo.remove_pending_subscriber(user_id)


class BotUserService:
    def __init__(self, repo: Repository):
        self.repo = repo

    def get_user(self, user_id: int) -> BotUser | None:
        return self.repo.get_bot_user(user_id)

    def save_user_info(self, user: BotUser) -> None:
        self.repo.save_bot_user_info(user)
