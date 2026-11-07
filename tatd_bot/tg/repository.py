import time

from redis import asyncio as redis

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

    async def add_subscriber(self, user_id: int) -> None:
        await self.r.sadd(SUBSCRIBERS, user_id)

    async def remove_subscriber(self, user_id: int) -> None:
        await self.r.srem(SUBSCRIBERS, user_id)

    async def is_subscriber(self, user_id: int) -> bool:
        return bool(await self.r.sismember(SUBSCRIBERS, user_id))

    async def get_subscribers(self) -> list:
        subscribers = await self.r.smembers(SUBSCRIBERS)
        return [int(subscriber) for subscriber in subscribers]

    async def add_pending_subscriber(self, user_id: int) -> None:
        await self.r.zadd(PENDING_SUBSCRIBERS, {user_id: time.time()})

    async def remove_pending_subscriber(self, user_id: int) -> None:
        await self.r.zrem(PENDING_SUBSCRIBERS, user_id)

    async def is_pending_subscriber(self, user_id: int) -> bool:
        return bool(await self.r.zscore(PENDING_SUBSCRIBERS, user_id))

    async def get_pending_subscribers(self) -> list[int] | None:
        pending_subscribers = await self.r.zrange(PENDING_SUBSCRIBERS, 0, -1)
        return [int(user_id) for user_id in pending_subscribers]

    async def get_pending_subscriber(self) -> int | None:
        result = await self.r.zrange(PENDING_SUBSCRIBERS, 0, 0)
        if not result:
            return None
        return int(result[0])

    async def save_bot_user_info(self, bot_user: BotUser) -> None:
        key = self._make_redis_key(BOT_USERS_INFO, user_id=bot_user.id)
        await self.r.hset(key, mapping=map_bot_user_to_redis(bot_user))

    async def get_bot_user(self, user_id: int) -> BotUser | None:
        key = self._make_redis_key(BOT_USERS_INFO, user_id=user_id)
        bot_user_data = await self.r.hgetall(key)
        if bot_user_data:
            return map_redis_to_bot_user(user_id, bot_user_data)
        return None

    async def set_bot_user_status(self, user_id: int, status: str) -> None:
        key = self._make_redis_key(BOT_USERS_INFO, user_id=user_id)
        bot_user = await self.r.hgetall(key)
        if bot_user:
            await self.r.hset(key, "status", status)
