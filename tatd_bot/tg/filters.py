from aiogram.filters import BaseFilter
from aiogram.types import Message

from tatd_bot.config.settings import ADMIN_ID


class IsAdmin(BaseFilter):
    def __init__(self, admin_id):
        self.admin_id = admin_id

    def __call__(self, message: Message):
        return message.from_user.id == self.admin_id


class HasText(BaseFilter):
    def __init__(self, text):
        self.text = text

    def __call__(self, message: Message):
        return self.text in message.text


def is_admin(message: Message):
    return message.from_user.id == ADMIN_ID


def has_accept_text(message: Message):
    return "Принять" in message.text
