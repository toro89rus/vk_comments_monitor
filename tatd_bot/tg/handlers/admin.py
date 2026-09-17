import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

import tatd_bot.tg.keyboards.keyboards as KEYBOARDS
from tatd_bot.tg import lexicon as LEXICON
from tatd_bot.tg.filters.filters import IsAdmin
from tatd_bot.tg.services.services import TgSubscriptionService
from tatd_bot.tg.states.states import AdminStates

logger = logging.getLogger(__name__)


admin_router = Router()


@admin_router.message(IsAdmin(), F.text == LEXICON.Button.REVIEW_PENDING_SUBS)
async def review_applications(
    message: Message,
    subsciption_service: TgSubscriptionService,
    state: FSMContext,
):
    applications = subsciption_service.get_pending_subscribers()
    if not applications:
        await message.answer(LEXICON.Message.NO_PENDING_APPLICATIONS)
    else:
        await state.set_state(AdminStates.reviewing_applications)
        await message.answer(
            LEXICON.Message.PENDING_APPLICATIONS_LEN.format(
                len=len(applications)
            )
        )
        await send_application(message, subsciption_service, state)


async def send_application(
    message: Message,
    subsciption_service: TgSubscriptionService,
    state: FSMContext,
):
    application_user = subsciption_service.get_pending_application_user()
    if not application_user:
        await message.answer(
            LEXICON.Message.NO_PENDING_APPLICATIONS,
            reply_markup=KEYBOARDS.ADMIN_PANEL,
        )
        await state.set_state(default_state)
    else:
        await message.answer(
            LEXICON.Message.APPLICATION.format(
                user_name=application_user.full_name
            ),
            reply_markup=KEYBOARDS.ADMIN_REVIEW_PENDING,
        )
        await state.update_data(application_user_id=application_user.id)


@admin_router.message(
    IsAdmin(),
    StateFilter(AdminStates.reviewing_applications),
    F.text == LEXICON.Button.ACCEPT_SUB,
)
async def accept_subscriber(
    message: Message,
    subsciption_service: TgSubscriptionService,
    state: FSMContext,
    bot: Bot,
):
    application_user_id: int | None = await state.get_value(
        "application_user_id"
    )
    if application_user_id:
        subsciption_service.accept_subscriber(application_user_id)
        await bot.send_message(
            application_user_id, LEXICON.Message.SUB_APPLICATION_ACCEPTED
        )
    await state.set_data({})
    await send_application(message, subsciption_service, state)


@admin_router.message(
    IsAdmin(),
    StateFilter(AdminStates.reviewing_applications),
    F.text == LEXICON.Button.DECLINE_SUB,
)
async def decline_subscriber(
    message: Message,
    subsciption_service: TgSubscriptionService,
    state: FSMContext,
    bot: Bot,
):
    application_user_id: int | None = await state.get_value(
        "application_user_id"
    )
    if application_user_id:
        subsciption_service.decline_subscriber(application_user_id)
        await bot.send_message(
            application_user_id, LEXICON.Message.SUB_APPLICATION_DECLINED
        )
    await state.set_data({})
    await send_application(message, subsciption_service, state)
