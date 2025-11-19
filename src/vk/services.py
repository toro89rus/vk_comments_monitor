import src.cache as cache
from src.vk.models import Group, User, Post


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
