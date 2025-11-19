from datetime import date, timedelta

from src.repository import repo
import src.vk.api as vk_api
from src.logger import logger
from src.vk.mappers import (
    to_comment_from_vk,
    to_post_from_vk,
    to_reply_from_vk,
    update_users_from_vk,
    update_groups_from_vk
)
from src.vk.models import Comment, Post, Reply
from src.vk.services import update_group_names_cache, update_user_names_cache

logger = logger.getChild(__name__)


def get_new_comments() -> list[Post]:
    logger.info("Started new comments collecting")
    recent_posts = get_recent_posts_with_comments()
    posts_with_new_comments = []
    for post in recent_posts:
        if post_new_comments := get_new_comments_for_post(post):
            posts_with_new_comments.append(post_new_comments)
    if posts_with_new_comments:
        authors_ids = collect_author_ids(posts_with_new_comments)
        update_authors_names(authors_ids)
    return posts_with_new_comments


def get_recent_posts_with_comments(days: int = 7) -> list:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    posts = vk_api.get_posts()
    recent_posts_with_comments = []
    for post in posts:
        post_date = date.fromtimestamp(post["date"])
        post_has_comments = post["comments"]["count"] > 0
        if post_has_comments and post_date >= start_date:
            recent_posts_with_comments.append(post)
    return recent_posts_with_comments


def get_new_comments_for_post(vk_post) -> Post:
    post_new_comments = []
    post_comments = vk_api.get_comments(vk_post["id"])

    for comment in post_comments:
        if comment["text"] != "":
            formatted_comment = format_comment(comment)
            if formatted_comment:
                post_new_comments.append(formatted_comment)

    if post_new_comments:
        return to_post_from_vk(vk_post, post_new_comments)

    return None


def format_comment(vk_comment: dict) -> Comment:

    formatted_comment = to_comment_from_vk(vk_comment)

    if vk_comment["thread"]["count"] > 0:
        formatted_comment.replies = get_new_replies(vk_comment)
    if formatted_comment.has_new_activity():
        return formatted_comment
    return None


def get_new_replies(vk_comment) -> list[Reply]:
    last_reply_id = int(repo.get_last_reply_id(vk_comment["id"]) or 0)
    new_replies = []
    vk_replies = vk_comment["thread"]["items"]
    for reply in vk_replies:
        if reply["id"] > last_reply_id:
            serialized_reply = to_reply_from_vk(reply)
            if serialized_reply.text:
                new_replies.append(serialized_reply)
        else:
            break
    return new_replies


def collect_author_ids(posts: list[Post]) -> dict[str, set]:
    users_ids, groups_ids = set(), set()
    author_type_mapping = {"user": users_ids, "group": groups_ids}
    for post in posts:
        for comment in post.comments:
            if not comment.author.name:
                author_id = comment.author.id
                author_type_mapping[comment.author.kind].add(author_id)
            for reply in comment.replies:
                if not reply.author.name:
                    author_id = reply.author.id
                    author_type_mapping[reply.author.kind].add(author_id)

                if not reply.reply_to.name:
                    reply_to_id = reply.reply_to.id
                    author_type_mapping[reply.reply_to.kind].add(reply_to_id)
    return {"users_ids": users_ids, "groups_ids": groups_ids}


def update_authors_names(authors_ids: dict) -> None:

    users_to_fetch = authors_ids["users_ids"]
    groups_to_fetch = authors_ids["groups_ids"]

    if users_to_fetch:
        vk_users = vk_api.get_users_names(users_to_fetch)

        update_users_from_vk(vk_users)
        update_user_names_cache(vk_users)

    if groups_to_fetch:
        vk_groups = vk_api.get_groups_names(groups_to_fetch)

        update_groups_from_vk(vk_groups)
        update_group_names_cache(vk_groups)
