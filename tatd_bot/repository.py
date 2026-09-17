import time

import redis

from tatd_bot.tg.mappers.mappers import (
    map_bot_user_to_redis,
    map_redis_to_bot_user,
)
from tatd_bot.tg.models.models import BotUser

SUBSCRIBERS = "subscribers"
PENDING_SUBSCRIBERS = "pending_subscribers"
BOT_USERS_INFO = "bot_user:{user_id}"
COMMENT_TEMPLATE = "comment:{comment_id}"
USER_TEMPLATE = "user:{user_id}"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"

USER_TTL = 2592000
COMMENT_TTL = 8 * 24 * 60 * 60


class Repository:

    def __init__(self, redis_host):
        self.r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

    def _make_redis_key(self, template_name: str, **kwargs: dict) -> str:
        return template_name.format(**kwargs)

    def get_user(self, user_id: int) -> dict[str, str]:
        key = self._make_redis_key(USER_TEMPLATE, user_id=user_id)
        return self.r.hgetall(key)

    def save_user(
        self, user_id: int, first_name: str, last_name: str, gender: str
    ) -> None:
        key = self._make_redis_key(USER_TEMPLATE, user_id=user_id)
        self.r.hset(
            key,
            mapping={
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
            },
        )

        self.r.expire(key, USER_TTL)

    def get_group_name(self, group_id: int) -> str | None:
        key = self._make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        return self.r.hget(key, "name")

    def save_group_name(self, group_id: int, group_name: str) -> None:
        key = self._make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        self.r.hset(key, "name", group_name)
        self.r.expire(key, USER_TTL)

    def is_comment_processed(self, comment_id: int) -> bool:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        value = self.r.hget(key, "is_processed")
        return value == "1"

    def process_comment(self, comment_id: int) -> None:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        self.r.hset(key, "is_processed", 1)
        self.r.expire(key, COMMENT_TTL)

    def save_last_reply_id(self, comment_id: int, reply_id: int) -> None:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        self.r.hset(key, "last_reply_id", reply_id)
        self.r.expire(key, COMMENT_TTL)

    def get_last_reply_id(self, comment_id: int) -> int | None:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        value = self.r.hget(key, "last_reply_id")
        if value:
            return int(value)
        return None

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
