import asyncio

from tatd_bot.logger import logger
from tatd_bot.tg.bot_runner import dp, monitor_vk_comments, tatd_bot

logger = logger.getChild(__name__)


async def run_bot():
    logger.info("Bot started")
    asyncio.create_task(monitor_vk_comments())
    await dp.start_polling(tatd_bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
