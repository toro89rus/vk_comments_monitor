import asyncio

from tatd_bot.logger import logger
from tatd_bot.tg.bot_runner import dp, monitor_vk_comments, tatd_bot

logger = logger.getChild(__name__)


async def monitor_vk_comments_safe():
    while True:
        try:
            await monitor_vk_comments()
        except Exception:
            logger.exception("VK monitor crashed")
            await asyncio.sleep(60 * 5)


async def run_bot():
    logger.info("Bot started")
    asyncio.create_task(monitor_vk_comments_safe())
    await dp.start_polling(tatd_bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
