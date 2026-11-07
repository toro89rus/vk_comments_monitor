from enum import Enum

from tatd_bot.config import AppConfig
from tatd_bot.tg.models import BotUser, BotUserStatus
from tatd_bot.tg.repository import TgRepository


class CreateSubRequestResult(Enum):
    ALREADY_SUBBED = "already_subscribed"
    ALREADY_PENDING = "already_pending"
    REQUEST_CREATED = "request_created"


class UnsubscribeResult(Enum):
    UNSUBSCRIBED = "unsubscribed"
    NOT_SUBSCRIBED = "not_subscribed"


class TgSubscriptionService:
    def __init__(self, config: AppConfig, repo: TgRepository):
        self.config = config
        self.repo = repo

    async def request_subscription(
        self, user: BotUser
    ) -> CreateSubRequestResult:
        if await self.repo.is_subscriber(user.id):
            return CreateSubRequestResult.ALREADY_SUBBED
        if await self.repo.is_pending_subscriber(user.id):
            return CreateSubRequestResult.ALREADY_PENDING
        user.status = BotUserStatus.PENDING
        await self.repo.save_bot_user_info(user)
        await self.repo.add_pending_subscriber(user.id)
        return CreateSubRequestResult.REQUEST_CREATED

    async def unsubscribe(self, user: BotUser) -> UnsubscribeResult:
        if await self.repo.is_subscriber(user.id):
            await self.repo.remove_subscriber(user.id)
            user.status = BotUserStatus.UNSUBSCRIBED
            await self.repo.save_bot_user_info(user)
            return UnsubscribeResult.UNSUBSCRIBED

        else:
            return UnsubscribeResult.NOT_SUBSCRIBED

    async def get_pending_subscribers(self):
        return await self.repo.get_pending_subscribers()

    async def get_pending_application_user(self) -> BotUser | None:
        user_id = await self.repo.get_pending_subscriber()
        if user_id:
            return await self.repo.get_bot_user(user_id)
        return None

    async def accept_subscriber(self, user_id: int) -> None:
        await self.repo.add_subscriber(user_id)
        await self.repo.set_bot_user_status(
            user_id, BotUserStatus.SUBSCRIBED.value
        )
        await self.repo.remove_pending_subscriber(user_id)

    async def decline_subscriber(self, user_id: int) -> None:
        await self.repo.set_bot_user_status(
            user_id, BotUserStatus.REJECTED.value
        )
        await self.repo.remove_pending_subscriber(user_id)


class BotUserService:
    def __init__(self, repo: TgRepository):
        self.repo = repo

    async def get_user(self, user_id: int) -> BotUser | None:
        return await self.repo.get_bot_user(user_id)

    async def save_user_info(self, user: BotUser) -> None:
        await self.repo.save_bot_user_info(user)
