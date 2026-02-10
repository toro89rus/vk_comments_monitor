import asyncio

from tatd_bot.tg.bot_runner import dp, monitor_vk_comments, tatd_bot


async def run_bot():
    asyncio.create_task(monitor_vk_comments())
    await dp.start_polling(tatd_bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
