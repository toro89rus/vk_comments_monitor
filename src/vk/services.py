from src.repository import repo
from src.vk.models import Post
from src.vk.registry import authors_registry


def update_comments_cache(posts: list[Post]) -> None:
    for post in posts:
        for comment in post.comments:
            if comment.is_new:
                repo.process_comment(comment.id)
            if comment.replies:
                repo.save_last_reply_id(comment.id, comment.replies[-1].id)


def update_user_names_cache(vk_users: list[dict]) -> None:
    for vk_user in vk_users:
        user = authors_registry.get_existing_user(vk_user["id"])
        repo.save_user(
            user.id,
            user.first_name,
            user.last_name,
            user.gender,
        )


def update_group_names_cache(vk_groups: list[dict]) -> None:
    for vk_group in vk_groups:
        group = authors_registry.get_existing_group(vk_group["id"])
        repo.save_group_name(group.id, group.name)
