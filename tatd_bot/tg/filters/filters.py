from aiogram.filters import BaseFilter
from aiogram.types import Message

from tatd_bot.config import AppConfig


class IsAdmin(BaseFilter):

    async def __call__(self, message: Message, config: AppConfig):
        return message.from_user.id == config.tg.admin_id
