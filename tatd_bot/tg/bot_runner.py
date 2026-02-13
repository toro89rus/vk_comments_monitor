import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import tatd_bot.tg.buttons as buttons
import tatd_bot.tg.filters as filters
from tatd_bot.config.settings import (
    ADMIN_ID,
    TG_API_TOKEN,
    VK_MONITOR_UPDATE_DELAY,
)
from tatd_bot.logger import logger
from tatd_bot.repository import repo
from tatd_bot.tg.formatters import format_comment, format_post, format_reply
from tatd_bot.vk.comments_parser import get_new_comments
from tatd_bot.vk.models import Post
from tatd_bot.vk.services import update_comments_cache

logger = logger.getChild(__name__)


tatd_bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[[buttons.subscribe, buttons.unsubscribe]],
    resize_keyboard=True,
)


@dp.message(Command(commands="start"))
async def process_start(message: Message):
    user = message.from_user.full_name
    logger.info(f"{user} sent start command")
    await message.answer(
        text="Подпишись для получения уведомлений", reply_markup=keyboard
    )


@dp.message(filters.is_admin, filters.has_accept_text)
async def accept_subscriber(message: Message):
    chat_id = int(message.text.split()[-1])
    repo.add_subscriber(chat_id)
    await tatd_bot.send_message(chat_id, text="Ваша заявка одобрена")


@dp.message(F.text == "Подписаться")
async def process_subscribe_button(message: Message):
    user = message.from_user.full_name
    chat_id = message.chat.id
    logger.info(f"{user} pushed subscribe button")
    if repo.is_subscriber(chat_id):
        await message.answer(text="Подписка уже активна")
    else:
        accept_subscriber = KeyboardButton(text=f"Принять заявку от {chat_id}")
        decline_subscriber = KeyboardButton(
            text=f"Отклонить заявку от {chat_id}"
        )
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[accept_subscriber, decline_subscriber]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        text = f"Заявка от {message.from_user.full_name}"
        await tatd_bot.send_message(ADMIN_ID, text=text, reply_markup=keyboard)
        logger.info("Subscribe application sent")
        await message.answer(
            "Заявка отправлена. Я сообщу когда она будет обработана"
        )


@dp.message(F.text == "Отписаться")
async def process_unsubscribe_button(message: Message):
    user = message.from_user.full_name
    chat_id = int(message.chat.id)
    logger.info(f"{user} pushed subscribe button")
    repo.remove_subscriber(chat_id)
    await message.answer(text="Вы успешно отписались", reply_markup=keyboard)
    await tatd_bot.send_message(ADMIN_ID, f"{user} отписался")


async def send_to_subscribers(vk_comments) -> None:
    subscribers_ids = repo.get_subscribers()
    tasks = (
        send_new_comments(vk_comments, subscriber_id)
        for subscriber_id in subscribers_ids
    )
    await asyncio.gather(*tasks)
    logger.info(f"New comments sent to {len(subscribers_ids)}")


async def send_new_comments(vk_comments: list[Post], chat_id: int) -> None:
    for post in vk_comments:
        await tatd_bot.send_message(
            chat_id, format_post(post), parse_mode="html"
        )
        for comment in post.comments:
            await tatd_bot.send_message(chat_id, format_comment(comment))
            for reply in comment.replies:
                await tatd_bot.send_message(chat_id, format_reply(reply))


async def monitor_vk_comments():
    while True:
        logger.info("Started comments motinoring")
        new_vk_comments = get_new_comments()
        if new_vk_comments:
            total_comments = sum(
                len(post.comments) for post in new_vk_comments
            )
            logger.info(
                f"Collected {len(new_vk_comments)} posts",
                f" with {total_comments} comments",
            )
            await send_to_subscribers(new_vk_comments)
            update_comments_cache(new_vk_comments)
            logger.info("New comments sent")
        else:
            logger.info("No new comments found")
        logger.info("Finished comments monitoring")
        await asyncio.sleep(VK_MONITOR_UPDATE_DELAY)
