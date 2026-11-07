import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

import tatd_bot.tg.keyboards.keyboards as KEYBOARDS
from tatd_bot.config.config import AppConfig
from tatd_bot.tg import lexicon as LEXICON
from tatd_bot.tg.mappers.mappers import map_tg_to_bot_user
from tatd_bot.tg.services.services import (
    BotUserService,
    CreateSubRequestResult,
    TgSubscriptionService,
    UnsubscribeResult,
)

user_router = Router()

logger = logging.getLogger(__name__)


@user_router.message(Command(commands="start"))
async def process_start(
    message: Message, bot_user_service: BotUserService, config: AppConfig
):
    user = message.from_user
    bot_user = bot_user_service.get_user(user.id)
    if not bot_user:
        bot_user = map_tg_to_bot_user(user)
        bot_user_service.save_user_info(bot_user)

    logger.info("%s sent start command", bot_user.full_name)
    keyboard = (
        KEYBOARDS.ADMIN_PANEL
        if user.id == config.tg.admin_id
        else KEYBOARDS.USER_SUBSCRIBE
    )
    await message.answer(text=LEXICON.Message.WELCOME, reply_markup=keyboard)


@user_router.message(F.text == LEXICON.Button.SUBSCRIBE)
async def process_subscribe_button(
    message: Message,
    bot: Bot,
    subsciption_service: TgSubscriptionService,
    config: AppConfig,
    bot_user_service: BotUserService,
):
    tg_user = message.from_user
    logger.info("%s pushed subscribe button", tg_user.full_name)
    user = bot_user_service.get_user(tg_user.id)
    if not user:
        user = map_tg_to_bot_user(tg_user)
        bot_user_service.save_user_info(user)

    result = await subsciption_service.request_subscription(user)
    if result == CreateSubRequestResult.ALREADY_SUBBED:
        await bot.send_message(user.id, LEXICON.Message.ALREADY_SUBBED)
    elif result == CreateSubRequestResult.ALREADY_PENDING:
        await bot.send_message(user.id, LEXICON.Message.ALREADY_PENDING)
    else:
        logger.info("Subscribe application sent")
        await bot.send_message(
            config.tg.admin_id,
            LEXICON.Message.APPLICATION_FROM.format(name=user.full_name),
        )
        await bot.send_message(
            chat_id=user.id, text=LEXICON.Message.SUB_APPLICATION_SENT
        )


@user_router.message(F.text == LEXICON.Button.UNSUBSCRIBE)
async def process_unsubscribe_button(
    message: Message,
    subsciption_service: TgSubscriptionService,
    bot: Bot,
    config: AppConfig,
):
    user = map_tg_to_bot_user(message.from_user)
    logger.info("%s pushed unsubscribe button", user.full_name)
    result = await subsciption_service.unsubscribe(user)
    keyboard = (
        KEYBOARDS.ADMIN_PANEL
        if user.id == config.tg.admin_id
        else KEYBOARDS.USER_SUBSCRIBE
    )
    if result == UnsubscribeResult.NOT_SUBSCRIBED:
        await bot.send_message(
            user.id,
            LEXICON.Message.NOT_SUBBED,
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(
            user.id,
            LEXICON.Message.UNSUBBED,
            reply_markup=keyboard,
        )
        await bot.send_message(
            config.tg.admin_id,
            LEXICON.Message.USER_UNSUBBED.format(user_name=user.full_name),
        )
