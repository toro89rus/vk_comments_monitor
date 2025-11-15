import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


IS_COMMENT_PROCCESSED_KEY_TEMPLATE = "comment:{comment_id}"
REPLY_ID_TEMPLATE = "comment:{comment_id}:latest_reply"
USER_NAME_KEY_TEMPLATE = "user:{user_id}:name"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"


def _make_redis_key(template_name: str, **kwargs: dict) -> str:
    return template_name.format(**kwargs)


def get_user_name(user_id: int) -> str | None:
    key = _make_redis_key(USER_NAME_KEY_TEMPLATE, user_id=user_id)
    return r.get(key)


def save_user_name(user_id: int, user_name: str) -> None:
    key = _make_redis_key(USER_NAME_KEY_TEMPLATE, user_id=user_id)
    r.set(key, user_name, ex=2592000)


def get_group_name(group_id: int) -> str | None:
    key = _make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
    return r.get(key)


def save_group_name(group_id: int, group_name: str) -> None:
    key = _make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
    r.set(key, group_name, ex=2592000)


def is_comment_proccessed(comment_id: int) -> bool:
    key = _make_redis_key(
        IS_COMMENT_PROCCESSED_KEY_TEMPLATE, comment_id=comment_id
    )
    return bool(int(r.get(key) or 0))


def proccess_comment(comment_id: int) -> None:
    key = _make_redis_key(
        IS_COMMENT_PROCCESSED_KEY_TEMPLATE, comment_id=comment_id
    )
    r.set(key, 1)


def save_last_reply_id(comment_id: int, reply_id: int) -> None:
    key = _make_redis_key(REPLY_ID_TEMPLATE, comment_id=comment_id)
    r.set(key, reply_id, ex=604800)


def get_last_reply_id(comment_id):
    key = _make_redis_key(REPLY_ID_TEMPLATE, comment_id=comment_id)
    return r.get(key)
