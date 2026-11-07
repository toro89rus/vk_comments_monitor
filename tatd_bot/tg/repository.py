import time

import redis

from tatd_bot.tg.mappers import (
    map_bot_user_to_redis,
    map_redis_to_bot_user,
)
from tatd_bot.tg.models import BotUser

SUBSCRIBERS = "subscribers"
PENDING_SUBSCRIBERS = "pending_subscribers"
BOT_USERS_INFO = "bot_user:{user_id}"


class TgRepository:
    def __init__(self, client: redis.Redis):
        self.r = client

    def _make_redis_key(self, template_name: str, **kwargs: dict) -> str:
        return template_name.format(**kwargs)

    def add_subscriber(self, user_id: int) -> None:
        self.r.sadd(SUBSCRIBERS, user_id)

    def remove_subscriber(self, user_id: int) -> None:
        self.r.srem(SUBSCRIBERS, user_id)

    def is_subscriber(self, user_id: int) -> bool:
        return bool(self.r.sismember(SUBSCRIBERS, user_id))

    def get_subscribers(self) -> list:
        subscribers = self.r.smembers(SUBSCRIBERS)
        return [int(subscriber) for subscriber in subscribers]

    def add_pending_subscriber(self, user_id: int) -> None:
        self.r.zadd(PENDING_SUBSCRIBERS, {user_id: time.time()})

    def remove_pending_subscriber(self, user_id: int) -> None:
        self.r.zrem(PENDING_SUBSCRIBERS, user_id)

    def is_pending_subscriber(self, user_id: int) -> bool:
        return bool(self.r.zscore(PENDING_SUBSCRIBERS, user_id))

    def get_pending_subscribers(self) -> list[int] | None:
        pending_subscribers = self.r.zrange(PENDING_SUBSCRIBERS, 0, -1)
        return [int(user_id) for user_id in pending_subscribers]

    def get_pending_subscriber(self) -> int | None:
        result = self.r.zrange(PENDING_SUBSCRIBERS, 0, 0)
        if not result:
            return None
        return int(result[0])

    def save_bot_user_info(self, bot_user: BotUser) -> None:
        key = self._make_redis_key(BOT_USERS_INFO, user_id=bot_user.id)
        self.r.hset(key, mapping=map_bot_user_to_redis(bot_user))

    def get_bot_user(self, user_id: int) -> BotUser | None:
        key = self._make_redis_key(BOT_USERS_INFO, user_id=user_id)
        bot_user_data = self.r.hgetall(key)
        if bot_user_data:
            return map_redis_to_bot_user(user_id, bot_user_data)
        return None

    def set_bot_user_status(self, user_id: int, status: str) -> None:
        key = self._make_redis_key(BOT_USERS_INFO, user_id=user_id)
        bot_user = self.r.hgetall(key)
        if bot_user:
            self.r.hset(key, "status", status)
