import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

import tatd_bot.tg.keyboards as KEYBOARDS
from tatd_bot.tg import lexicon as LEXICON
from tatd_bot.tg.filters.filters import IsAdmin
from tatd_bot.tg.handlers.admin import (
    accept_subscriber,
    decline_subscriber,
    review_applications,
)
from tatd_bot.tg.handlers.user import (
    process_start,
    process_subscribe_button,
    process_unsubscribe_button,
)
from tatd_bot.tg.models import BotUserStatus
from tatd_bot.tg.services import (
    BotUserService,
    TgSubscriptionService,
)
from tests.conftest import ADMIN_ID
from tests.tg.fakes import FakeBot, FakeMessage, tg_user

USER_ID = 1


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def subscription_service(app_config, repo):
    return TgSubscriptionService(app_config, repo)


@pytest.fixture
def bot_user_service(repo):
    return BotUserService(repo)


@pytest.fixture
def admin_state():
    key = StorageKey(bot_id=1, chat_id=ADMIN_ID, user_id=ADMIN_ID)
    return FSMContext(storage=MemoryStorage(), key=key)


def message_from(user_id: int, first_name: str = "Иван") -> FakeMessage:
    return FakeMessage(from_user=tg_user(user_id, first_name))


async def subscribe(user_id, bot, subscription_service, app_config, service):
    await process_subscribe_button(
        message_from(user_id, f"Иван{user_id}"),
        bot,
        subscription_service,
        app_config,
        service,
    )


class TestIsAdmin:
    async def test_admin(self, app_config):
        assert await IsAdmin()(message_from(ADMIN_ID), app_config) is True

    async def test_not_admin(self, app_config):
        assert await IsAdmin()(message_from(USER_ID), app_config) is False


class TestStart:
    async def test_new_user_is_saved(self, bot_user_service, app_config, repo):
        message = message_from(USER_ID)

        await process_start(message, bot_user_service, app_config)

        assert repo.get_bot_user(USER_ID).status is BotUserStatus.NEW
        assert message.answers[0].text == LEXICON.Message.WELCOME
        assert message.answers[0].reply_markup is KEYBOARDS.USER_SUBSCRIBE

    async def test_known_user_is_not_overwritten(
        self, bot_user_service, app_config, repo
    ):
        repo.add_subscriber(USER_ID)
        await process_start(message_from(USER_ID), bot_user_service, app_config)
        repo.set_bot_user_status(USER_ID, BotUserStatus.SUBSCRIBED.value)

        await process_start(
            message_from(USER_ID, "Пётр"), bot_user_service, app_config
        )

        user = repo.get_bot_user(USER_ID)
        assert user.status is BotUserStatus.SUBSCRIBED
        assert user.full_name == "Иван Петров"

    async def test_admin_gets_admin_panel(self, bot_user_service, app_config):
        message = message_from(ADMIN_ID)

        await process_start(message, bot_user_service, app_config)

        assert message.answers[0].reply_markup is KEYBOARDS.ADMIN_PANEL


class TestSubscribeButton:
    async def test_request_is_sent_to_admin(
        self, bot, subscription_service, app_config, bot_user_service, repo
    ):
        await subscribe(
            USER_ID, bot, subscription_service, app_config, bot_user_service
        )

        assert repo.is_pending_subscriber(USER_ID) is True
        assert bot.texts_for(ADMIN_ID) == ["Заявка от Иван1 Петров"]
        assert bot.texts_for(USER_ID) == [LEXICON.Message.SUB_APPLICATION_SENT]

    async def test_repeated_request(
        self, bot, subscription_service, app_config, bot_user_service
    ):
        for _ in range(2):
            await subscribe(
                USER_ID,
                bot,
                subscription_service,
                app_config,
                bot_user_service,
            )

        assert bot.texts_for(USER_ID)[-1] == LEXICON.Message.ALREADY_PENDING
        assert len(bot.texts_for(ADMIN_ID)) == 1

    async def test_already_subscribed(
        self, bot, subscription_service, app_config, bot_user_service, repo
    ):
        repo.add_subscriber(USER_ID)

        await subscribe(
            USER_ID, bot, subscription_service, app_config, bot_user_service
        )

        assert bot.texts_for(USER_ID) == [LEXICON.Message.ALREADY_SUBBED]
        assert bot.texts_for(ADMIN_ID) == []


class TestUnsubscribeButton:
    async def test_unsubscribe(
        self, bot, subscription_service, app_config, repo
    ):
        repo.add_subscriber(USER_ID)

        await process_unsubscribe_button(
            message_from(USER_ID), subscription_service, bot, app_config
        )

        assert repo.is_subscriber(USER_ID) is False
        assert repo.get_bot_user(USER_ID).status is (BotUserStatus.UNSUBSCRIBED)
        assert bot.texts_for(USER_ID) == [LEXICON.Message.UNSUBBED]
        assert bot.texts_for(ADMIN_ID) == ["Иван Петров отписался"]

    async def test_not_subscribed(self, bot, subscription_service, app_config):
        await process_unsubscribe_button(
            message_from(USER_ID), subscription_service, bot, app_config
        )

        assert bot.texts_for(USER_ID) == [LEXICON.Message.NOT_SUBBED]
        assert bot.sent[0].reply_markup is KEYBOARDS.USER_SUBSCRIBE
        assert bot.texts_for(ADMIN_ID) == []


class TestReviewApplications:
    async def test_no_applications(self, subscription_service, admin_state):
        message = message_from(ADMIN_ID)

        await review_applications(message, subscription_service, admin_state)

        assert [a.text for a in message.answers] == [
            LEXICON.Message.NO_PENDING_APPLICATIONS
        ]
        assert await admin_state.get_state() is None

    async def test_review_shows_first_application(
        self,
        bot,
        subscription_service,
        app_config,
        bot_user_service,
        admin_state,
    ):
        for user_id in (1, 2):
            await subscribe(
                user_id,
                bot,
                subscription_service,
                app_config,
                bot_user_service,
            )
        message = message_from(ADMIN_ID)

        await review_applications(message, subscription_service, admin_state)

        assert [a.text for a in message.answers] == [
            "Всего заявок: 2",
            "Заявка от Иван1 Петров",
        ]
        assert message.answers[1].reply_markup is (
            KEYBOARDS.ADMIN_REVIEW_PENDING
        )
        assert (
            await admin_state.get_state()
            == "AdminStates:reviewing_applications"
        )
        assert await admin_state.get_value("application_user_id") == 1

    async def test_accept_then_decline_until_queue_is_empty(
        self,
        bot,
        subscription_service,
        app_config,
        bot_user_service,
        admin_state,
        repo,
    ):
        for user_id in (1, 2):
            await subscribe(
                user_id,
                bot,
                subscription_service,
                app_config,
                bot_user_service,
            )
        await review_applications(
            message_from(ADMIN_ID), subscription_service, admin_state
        )

        accept_message = message_from(ADMIN_ID)
        await accept_subscriber(
            accept_message, subscription_service, admin_state, bot
        )

        assert repo.is_subscriber(1) is True
        assert bot.texts_for(1)[-1] == LEXICON.Message.SUB_APPLICATION_ACCEPTED
        assert accept_message.answers[0].text == "Заявка от Иван2 Петров"
        assert await admin_state.get_value("application_user_id") == 2

        decline_message = message_from(ADMIN_ID)
        await decline_subscriber(
            decline_message, subscription_service, admin_state, bot
        )

        assert repo.get_bot_user(2).status is BotUserStatus.REJECTED
        assert bot.texts_for(2)[-1] == LEXICON.Message.SUB_APPLICATION_DECLINED
        assert decline_message.answers[0].text == (
            LEXICON.Message.NO_PENDING_APPLICATIONS
        )
        assert decline_message.answers[0].reply_markup is KEYBOARDS.ADMIN_PANEL
        assert await admin_state.get_state() == default_state.state

    async def test_accept_without_application_in_state(
        self, bot, subscription_service, admin_state, repo
    ):
        # например, после перезапуска бота данные FSM потеряны
        message = message_from(ADMIN_ID)

        await accept_subscriber(message, subscription_service, admin_state, bot)

        assert bot.sent == []
        assert message.answers[0].text == (
            LEXICON.Message.NO_PENDING_APPLICATIONS
        )
