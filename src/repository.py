import redis

COMMENT_TEMPLATE = "comment:{comment_id}"
USER_TEMPLATE = "user:{user_id}"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"

USER_TTL = 2592000
COMMENT_TTL = 604800


def make_redis_key(template_name: str, **kwargs: dict) -> str:
    return template_name.format(**kwargs)


class Repository:

    def __init__(self):
        self.r = redis.Redis(
            host="localhost", port=6379, decode_responses=True
        )

    def get_user(self, user_id: int) -> dict[str, str]:
        key = make_redis_key(USER_TEMPLATE, user_id=user_id)
        return self.r.hgetall(key)

    def save_user(
        self, user_id: int, first_name: str, last_name: str, gender: str
    ) -> None:
        key = make_redis_key(USER_TEMPLATE, user_id=user_id)
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
        key = make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        return self.r.hget(key, "name")

    def save_group_name(self, group_id: int, group_name: str) -> None:
        key = make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        self.r.set(key, "name", group_name)
        self.r.expire(key, USER_TTL)

    def is_comment_processed(self, comment_id: int) -> bool:
        key = make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        value = self.r.hget(key, "is_processed")
        return value == "1"

    def process_comment(self, comment_id: int) -> None:
        key = make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        self.r.hset(key, "is_processed", 1)
        self.r.expire(key, COMMENT_TTL)

    def save_last_reply_id(self, comment_id: int, reply_id: int) -> None:
        key = make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        self.r.hset(key, "last_reply_id", reply_id)
        self.r.expire(key, COMMENT_TTL)

    def get_last_reply_id(self, comment_id: int) -> int | None:
        key = make_redis_key(COMMENT_TEMPLATE, comment_id=comment_id)
        value = self.r.hget(key, "last_reply_id")
        if value:
            return int(value)
        return None


repo = Repository()
