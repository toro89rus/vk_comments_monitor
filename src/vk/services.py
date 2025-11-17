import src.cache as cache
from src.vk.models import Group, User, Post
from petrovich.enums import Gender

VK_TO_PETROVIC_GENDER_MAPPING = {1: Gender.FEMALE, 2: Gender.MALE, 0: None}


def make_author(uid: int) -> Group | User:

    if uid < 0:
        return Group(id=abs(uid), name=cache.get_group_name(uid))

    cached_user = cache.get_user(uid)
    if cached_user:
        first_name = cached_user["first_name"]
        last_name = cached_user["last_name"]
        gender = cached_user["gender"]
        return User(id, first_name, last_name, gender)

    return User(id=uid)


def map_users_gender(users):
    mapped_users = users.copy()
    for user in mapped_users.values():
        user["sex"] = VK_TO_PETROVIC_GENDER_MAPPING[user["sex"]]
    return mapped_users


def update_user(user: dict) -> None:
    pass


def update_comments_cache(posts: list[Post]) -> None:
    for post in posts:
        for comment in post.comments:
            if comment.is_new:
                cache.proccess_comment(comment.id)
            if comment.replies:
                cache.save_last_reply_id(comment.id, comment.replies[-1].id)


def update_user_names_cache(vk_users: list[dict]) -> None:
    for vk_user in vk_users:
        user = User.get_existing(vk_user["id"])
        cache.save_user(
            user.id,
            user.first_name,
            user.last_name,
            user.gender,
        )


def update_group_names_cache(vk_groups: dict) -> None:
    for vk_group in vk_groups:
        group = Group.get_existing(vk_group["id"])
        cache.save_group_name(group.id, group.name)
