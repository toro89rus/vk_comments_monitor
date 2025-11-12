import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


THREAD_KEY_TEMPLATE = "post:{post_id}:comment:{comment_id}:thread_comment"
USER_NAME_KEY_TEMPLATE = "user:{user_id}:name"
GROUP_NAME_KEY_TEMPLATE = "group:{group_id}:name"


def _make_redis_key(template_name, **kwargs) -> str:
    return template_name.format(**kwargs)


def load_thread_comment_id(post_id, comment_id):
    key = _make_redis_key(
        THREAD_KEY_TEMPLATE, post_id=post_id, comment_id=comment_id
    )
    value = r.get(key) or -1
    return int(value)


def save_thread_comment_id(post_id, comment_id, thread_comment_id):
    key = _make_redis_key(
        THREAD_KEY_TEMPLATE, post_id=post_id, comment_id=comment_id
    )
    r.set(key, thread_comment_id, ex=604800)


def load_user_name(user_id):
    key = _make_redis_key(USER_NAME_KEY_TEMPLATE, user_id=user_id)
    return r.get(key)


def save_user_name(user_id, user_name):
    key = _make_redis_key(USER_NAME_KEY_TEMPLATE, user_id=user_id)
    r.set(key, user_name, ex=2592000)


def load_group_name(group_id):
    key = _make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
    return r.get(key)


def save_group_name(group_id, group_name):
    key = _make_redis_key(GROUP_NAME_KEY_TEMPLATE, group_id=group_id)
    r.set(key, group_name, ex=2592000)
