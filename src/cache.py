import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


THREAD_KEY_TEMPLATE = "post:{post_id}:comment:{comment_id}:thread_comment"
USER_NAME_KEY_TEMPLATE = "user:{user_id}:name"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"


def _make_redis_key(template_name: str, **kwargs: dict) -> str:
    return template_name.format(**kwargs)


def load_thread_comment_id(post_id: int, comment_id: int) -> str | None:
    key = _make_redis_key(
        THREAD_KEY_TEMPLATE, post_id=post_id, comment_id=comment_id
    )
    return r.get(key)


def save_thread_comment_id(
    post_id: int, comment_id: int, thread_comment_id: int
) -> None:
    key = _make_redis_key(
        THREAD_KEY_TEMPLATE, post_id=post_id, comment_id=comment_id
    )
    r.set(key, thread_comment_id, ex=604800)


def load_user_name(user_id: int) -> str | None:
    key = _make_redis_key(USER_NAME_KEY_TEMPLATE, user_id=user_id)
    return r.get(key)


def save_user_name(user_id: int, user_name: str) -> None:
    key = _make_redis_key(USER_NAME_KEY_TEMPLATE, user_id=user_id)
    r.set(key, user_name, ex=2592000)


def load_group_name(group_id: int) -> str | None:
    key = _make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
    return r.get(key)


def save_group_name(group_id: int, group_name: str) -> None:
    key = _make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
    r.set(key, group_name, ex=2592000)
