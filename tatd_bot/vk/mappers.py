from petrovich.enums import Gender

from tatd_bot.utils.time_utils import get_msk_time
from tatd_bot.vk.models import Comment, Group, Post, User

VK_TO_PETROVIC_GENDER_MAPPING = {1: Gender.FEMALE, 2: Gender.MALE, 0: None}


def vk_to_post(vk_post: dict, comments: list[Comment]) -> Post:
    return Post(
        id=vk_post["id"],
        created_at=get_msk_time(vk_post["date"]),
        text=vk_post["text"],
        comments=comments,
    )


def vk_to_vk_user(vk_user: dict) -> User:
    return User(
        id=vk_user["id"],
        first_name=vk_user["first_name"],
        last_name=vk_user["last_name"],
        gender=VK_TO_PETROVIC_GENDER_MAPPING[vk_user["sex"]],
    )


def vk_to_vk_group(vk_group: dict) -> Group:
    return Group(id=vk_group["id"], name=vk_group["name"])


def vk_to_vk_user_base_data(vk_user: dict) -> dict:
    return {
        "first_name": vk_user["first_name"],
        "last_name": vk_user["last_name"],
        "gender": VK_TO_PETROVIC_GENDER_MAPPING[vk_user["sex"]],
    }
