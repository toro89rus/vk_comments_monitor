import asyncio

from aiogram import Bot, Dispatcher

from tatd_bot.config import load_config
from tatd_bot.logger import setup_logger
from tatd_bot.repository import Repository, create_redis_client
from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.tg.handlers.admin import admin_router
from tatd_bot.tg.handlers.user import user_router
from tatd_bot.tg.services import (
    BotUserService,
    TgSubscriptionService,
    VkCommentsMonitorService,
)
from tatd_bot.vk.api import VkApiService
from tatd_bot.vk.registry import AuthorsRegistry
from tatd_bot.vk.services import (
    VkAuthorService,
    VkFeedService,
    VkMessageService,
)


async def run_bot():
    config = load_config()
    logger = setup_logger(config.log_format, config.env)
    logger.info("Bot started")

    repo = Repository(create_redis_client(config.redis))
    tatd_bot = Bot(token=config.tg.token)
    dp = Dispatcher()

    formatter = TgMessageFormatter(config)
    vk_api_service = VkApiService(config)
    vk_authors_registry = AuthorsRegistry()
    vk_author_service = VkAuthorService(vk_authors_registry, repo)
    vk_message_service = VkMessageService(vk_author_service, repo)
    vk_feed_service = VkFeedService(
        vk_api_service, vk_author_service, vk_message_service, repo
    )
    vk_monitor_service = VkCommentsMonitorService(
        config=config,
        repo=repo,
        bot=tatd_bot,
        formatter=formatter,
        feed_service=vk_feed_service,
    )
    subscription_service = TgSubscriptionService(config, repo)
    bot_user_service = BotUserService(repo)

    dp["config"] = config
    dp["repo"] = repo
    dp["subscription_service"] = subscription_service
    dp["bot_user_service"] = bot_user_service

    dp.include_router(user_router)
    dp.include_router(admin_router)

    asyncio.create_task(vk_monitor_service.monitor())
    await dp.start_polling(tatd_bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
