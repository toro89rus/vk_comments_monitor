import asyncio
import logging

from aiogram import Bot

from tatd_bot.config import load_config
from tatd_bot.repository import Repository
from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.vk.api import VkApiService
from tatd_bot.vk.registry import AuthorsRegistry
from tatd_bot.vk.services import (
    VkAuthorService,
    VkFeedService,
    VkMessageService,
)


async def main():
    config = load_config()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("vk_comments")

    logger.info("SCRIPT STARTED")

    repo = Repository(config.redis.host)
    bot = Bot(token=config.tg.token)
    formatter = TgMessageFormatter(config)

    vk_api_service = VkApiService(config)
    authors_registry = AuthorsRegistry()
    author_service = VkAuthorService(authors_registry, repo)
    message_service = VkMessageService(author_service, repo)
    feed_service = VkFeedService(
        vk_api_service, author_service, message_service, repo
    )

    new_vk_comments = feed_service.get_new_comments()
    if new_vk_comments:  # noqa: PLR1702
        logger.info(
            "Collected %s posts with new comments", len(new_vk_comments)
        )
        subscribers_ids = repo.get_subscribers()
        for subscriber_id in subscribers_ids:
            for post in new_vk_comments:
                await bot.send_message(
                    subscriber_id,
                    formatter.format_post(post),
                    parse_mode="html",
                )
                for comment in post.comments:
                    await bot.send_message(
                        subscriber_id, formatter.format_comment(comment)
                    )
                    for reply in comment.replies:
                        await bot.send_message(
                            subscriber_id, formatter.format_reply(reply)
                        )
        feed_service.save_comments_cache(new_vk_comments)
        logger.info("New comments sent to %s subscribers", len(subscribers_ids))
    else:
        logger.info("No new comments found")

    await bot.session.close()
    logger.info("SCRIPT ENDED")


if __name__ == "__main__":
    asyncio.run(main())
