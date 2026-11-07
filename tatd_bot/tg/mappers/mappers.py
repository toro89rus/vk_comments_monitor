from aiogram.types import User

from tatd_bot.tg.models import BotUser, BotUserStatus


def map_bot_user_to_redis(bot_user: BotUser):
    return {
        "full_name": bot_user.full_name,
        "username": bot_user.username or "",
        "status": bot_user.status.value,
    }


def map_redis_to_bot_user(chat_id: int, data: dict) -> BotUser:
    return BotUser(
        id=chat_id,
        full_name=data["full_name"],
        username=data["username"],
        status=BotUserStatus(data["status"]),
    )


def map_tg_to_bot_user(
    tg_user: User, status: BotUserStatus = BotUserStatus.NEW
) -> BotUser:
    return BotUser(
        id=tg_user.id,
        full_name=tg_user.full_name,
        username=tg_user.username,
        status=status,
    )
