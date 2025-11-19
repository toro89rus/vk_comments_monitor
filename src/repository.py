import redis

IS_COMMENT_PROCCESSED_KEY_TEMPLATE = "comment:{comment_id}"
REPLY_ID_TEMPLATE = "comment:{comment_id}:latest_reply"
USER_TEMPLATE = "user:{user_id}"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"


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

        self.r.expire(key, 2592000)

    def get_group_name(self, group_id: int) -> str | None:
        key = make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        return self.r.get(key)

    def save_group_name(self, group_id: int, group_name: str) -> None:
        key = make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
        self.r.set(key, group_name, ex=2592000)

    def is_comment_proccessed(self, comment_id: int) -> bool:
        key = make_redis_key(
            IS_COMMENT_PROCCESSED_KEY_TEMPLATE, comment_id=comment_id
        )
        value = self.r.get(key)
        return value == "1"

    def proccess_comment(self, comment_id: int) -> None:
        key = make_redis_key(
            IS_COMMENT_PROCCESSED_KEY_TEMPLATE, comment_id=comment_id
        )
        self.r.set(key, 1)

    def save_last_reply_id(self, comment_id: int, reply_id: int) -> None:
        key = make_redis_key(REPLY_ID_TEMPLATE, comment_id=comment_id)
        self.r.set(key, reply_id, ex=604800)

    def get_last_reply_id(self, comment_id):
        key = make_redis_key(REPLY_ID_TEMPLATE, comment_id=comment_id)
        return self.r.get(key)


repo = Repository()
