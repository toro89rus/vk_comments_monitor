from datetime import date, datetime

from petrovich.enums import Gender

from src.repository import repo
from src.vk.models import Comment, Group, Post, Reply, User
from src.vk.text_formatting import format_comment_text, format_reply_text
from src.vk.registry import authors_registry

VK_TO_PETROVIC_GENDER_MAPPING = {1: Gender.FEMALE, 2: Gender.MALE, 0: None}


def to_comment_from_vk(vk_comment: dict) -> Comment:
    return make_message_entity(Comment, vk_comment)


def to_reply_from_vk(vk_comment: dict) -> Reply:
    return make_message_entity(Reply, vk_comment)


def make_message_entity(
    model_cls: Comment | Reply, data: dict
) -> Comment | Reply:
    base = parse_base(data)

    if model_cls is Comment:
        base["replies"] = []
        base["is_new"] = not repo.is_comment_proccessed(data["id"])
        base["text"] = format_comment_text(data["text"])

    if model_cls is Reply:
        base["reply_to"] = to_author_from_id(data["reply_to_user"])
        base["text"] = format_reply_text(data["text"])

    return model_cls(**base)


def parse_base(data: dict) -> dict:
    return {
        "id": data["id"],
        "created_at": datetime.fromtimestamp(data["date"]),
        "author": to_author_from_id(data["from_id"]),
    }


def to_author_from_id(uid: int) -> Group | User:

    if uid < 0:
        gid = abs(uid)
        return _make_group(gid)

    return _make_user(uid)


def _make_group(gid: int) -> Group:
    cached_local_group = authors_registry.get_existing_group(gid)
    if cached_local_group:
        return cached_local_group

    cached_external_group_name = repo.get_group_name(gid)
    if cached_external_group_name:
        group = Group(gid, cached_external_group_name)
        authors_registry.register_group(group)
        return group

    group = Group(gid)
    authors_registry.register_group(group)
    return group


def _make_user(uid: int) -> User:
    cached_local_user = authors_registry.get_existing_user(uid)
    if cached_local_user:
        return cached_local_user

    cached_external_user = repo.get_user(uid)
    if cached_external_user:
        first_name = cached_external_user["first_name"]
        last_name = cached_external_user["last_name"]
        gender = cached_external_user["gender"]
        user = User(uid, first_name, last_name, gender)
        authors_registry.register_user(user)
        return user

    user = User(uid)
    authors_registry.register_user(user)
    return user


def update_users_from_vk(vk_users: dict) -> None:
    for vk_user in vk_users:
        user = authors_registry.get_existing_user(vk_user["id"])
        # raise exception - didn't get user but there shouldn't be new users
        # at this point
        data = {
            "first_name": vk_user["first_name"],
            "last_name": vk_user["last_name"],
            "gender": VK_TO_PETROVIC_GENDER_MAPPING[vk_user["sex"]],
        }
        user.update(data)


def update_groups_from_vk(vk_groups: dict) -> None:
    for vk_group in vk_groups:
        group = authors_registry.get_existing_group(vk_group["id"])
        # raise exception - didn't get group but there shouldn't be new groups
        # at this point
        group.update(vk_group)


def to_post_from_vk(vk_post: dict, comments: list[Comment]) -> Post:
    post_date = date.fromtimestamp(vk_post["date"])
    return Post(
        id=vk_post["id"],
        created_at=post_date,
        text=vk_post["text"],
        comments=comments,
    )


def to_user_from_vk(vk_user: dict) -> User:
    return User(
        id=vk_user["id"],
        first_name=vk_user["first_name"],
        last_name=vk_user["last_name"],
        gender=VK_TO_PETROVIC_GENDER_MAPPING[vk_user["sex"]],
    )


def to_group_from_vk(vk_group: dict) -> Group:
    return Group(
        id=vk_group["id"],
        name=vk_group["name"]
    )
