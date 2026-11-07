from redis import asyncio as redis

COMMENT_TEMPLATE = "comment:{comment_id}"
USER_TEMPLATE = "user:{user_id}"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"

USER_TTL = 2592000
COMMENT_TTL = 8 * 24 * 60 * 60


class VkRepository:
    def __init__(self, client: redis.Redis):
        self.r = client

    def _make_redis_key(self, template_name: str, **kwargs: dict) -> str:
        return template_name.format(**kwargs)

    async def get_user(self, user_id: int) -> dict[str, str]:
        key = self._make_redis_key(USER_TEMPLATE, user_id=user_id)
        return await self.r.hgetall(key)

    async def save_user(
        self, user_id: int, first_name: str, last_name: str, gender: str
    ) -> None:
        key = self._make_redis_key(USER_TEMPLATE, user_id=user_id)
        await self.r.hset(
            key,
            mapping={
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
            },
        )

        await self.r.expire(key, USER_TTL)

    async def get_group_name(self, group_id: int) -> str | None:
        key = self._make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        return await self.r.hget(key, "name")

    async def save_group_name(self, group_id: int, group_name: str) -> None:
        key = self._make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        await self.r.hset(key, "name", group_name)
        await self.r.expire(key, USER_TTL)

    async def is_comment_processed(self, comment_id: int) -> bool:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        value = await self.r.hget(key, "is_processed")
        return value == "1"

    async def process_comment(self, comment_id: int) -> None:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        await self.r.hset(key, "is_processed", 1)
        await self.r.expire(key, COMMENT_TTL)

    async def save_last_reply_id(self, comment_id: int, reply_id: int) -> None:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        await self.r.hset(key, "last_reply_id", reply_id)
        await self.r.expire(key, COMMENT_TTL)

    async def get_last_reply_id(self, comment_id: int) -> int | None:
        key = self._make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        value = await self.r.hget(key, "last_reply_id")
        if value:
            return int(value)
        return None
