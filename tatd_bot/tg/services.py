from enum import Enum

from tatd_bot.config import AppConfig
from tatd_bot.repository import Repository
from tatd_bot.tg.models import BotUser, BotUserStatus


class CreateSubRequestResult(Enum):
    ALREADY_SUBBED = "already_subscribed"
    ALREADY_PENDING = "already_pending"
    REQUEST_CREATED = "request_created"


class UnsubscribeResult(Enum):
    UNSUBSCRIBED = "unsubscribed"
    NOT_SUBSCRIBED = "not_subscribed"


class TgSubscriptionService:
    def __init__(self, config: AppConfig, repo: Repository):
        self.config = config
        self.repo = repo

    async def request_subscription(
        self, user: BotUser
    ) -> CreateSubRequestResult:
        if self.repo.is_subscriber(user.id):
            return CreateSubRequestResult.ALREADY_SUBBED
        if self.repo.is_pending_subscriber(user.id):
            return CreateSubRequestResult.ALREADY_PENDING
        user.status = BotUserStatus.PENDING
        self.repo.save_bot_user_info(user)
        self.repo.add_pending_subscriber(user.id)
        return CreateSubRequestResult.REQUEST_CREATED

    async def unsubscribe(self, user: BotUser) -> UnsubscribeResult:
        if self.repo.is_subscriber(user.id):
            self.repo.remove_subscriber(user.id)
            user.status = BotUserStatus.UNSUBSCRIBED
            self.repo.save_bot_user_info(user)
            return UnsubscribeResult.UNSUBSCRIBED

        else:
            return UnsubscribeResult.NOT_SUBSCRIBED

    def get_pending_subscribers(self):
        return self.repo.get_pending_subscribers()

    def get_pending_application_user(self) -> BotUser | None:
        user_id = self.repo.get_pending_subscriber()
        if user_id:
            return self.repo.get_bot_user(user_id)
        return None

    def accept_subscriber(self, user_id: int) -> None:
        self.repo.add_subscriber(user_id)
        self.repo.set_bot_user_status(user_id, BotUserStatus.SUBSCRIBED.value)
        self.repo.remove_pending_subscriber(user_id)

    def decline_subscriber(self, user_id: int) -> None:
        self.repo.set_bot_user_status(user_id, BotUserStatus.REJECTED.value)
        self.repo.remove_pending_subscriber(user_id)


class BotUserService:
    def __init__(self, repo: Repository):
        self.repo = repo

    def get_user(self, user_id: int) -> BotUser | None:
        return self.repo.get_bot_user(user_id)

    def save_user_info(self, user: BotUser) -> None:
        self.repo.save_bot_user_info(user)
