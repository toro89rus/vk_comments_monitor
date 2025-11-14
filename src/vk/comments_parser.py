import re
from datetime import date, datetime, timedelta

import src.cache as cache
import src.vk.api as vk_api
from src.logger import logger
from src.vk.classes import Author, Comment, Post, Reply
from src.vk.text_formatting import format_reply_text, format_comment_text

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
        posts_with_new_comments = add_authors_names(
            posts_with_new_comments, authors_ids
        )
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


def get_new_comments_for_post(post) -> Post:
    post_id = post["id"]
    post_text = f"{post['text'][:100]}..."
    post_date = date.fromtimestamp(post["date"])
    post_new_comments = []
    post_comments = vk_api.get_comments(post_id)
    for comment in post_comments:
        formatted_comment = format_comment(comment)
        if formatted_comment:
            post_new_comments.append(formatted_comment)
    if post_new_comments:
        return Post(
            id=post_id,
            created_at=post_date,
            text=post_text,
            comments=post_new_comments,
        )

    return None


def format_comment(comment: dict):
    is_new = not cache.is_comment_proccessed(comment["id"])
    formatted_comment = Comment(
        **serialize_comment(comment), is_new=is_new, replies=[]
    )
    if comment["thread"]["count"] > 0:
        formatted_comment.replies = get_new_replies(comment)
    if formatted_comment.has_new_activity():
        return formatted_comment
    return None


def get_new_replies(comment) -> list[Reply]:
    last_reply_id = int(cache.get_last_reply_id(comment["id"]) or 0)
    new_replies = []
    replies = comment["thread"]["items"]
    for reply in replies:
        if reply["id"] > last_reply_id:
            serialized_reply = Reply(**serialize_reply(reply))
            if serialized_reply.text:
                new_replies.append(serialized_reply)
        else:
            break
    return new_replies


def serialize_comment(vk_comment: dict) -> Comment | None:
    comment_text = format_comment_text(vk_comment["text"])
    author = make_author(vk_comment["from_id"])
    return {
        "id": vk_comment["id"],
        "created_at": datetime.fromtimestamp(vk_comment["date"]),
        "author": author,
        "text": comment_text,
    }


def serialize_reply(vk_reply: dict) -> Reply:
    comment_text = format_reply_text(vk_reply["text"])
    author = make_author(vk_reply["from_id"])
    reply_to = make_author(vk_reply["reply_to_user"])
    return {
        "id": vk_reply["id"],
        "created_at": datetime.fromtimestamp(vk_reply["date"]),
        "author": author,
        "text": comment_text,
        "reply_to": reply_to,
    }


def collect_author_ids(posts: list[Post]) -> dict[str, set]:
    users_ids, groups_ids = set(), set()
    author_type_mapping = {"user": users_ids, "group": groups_ids}
    for post in posts:
        for comment in post.comments:
            if not comment.author.name:
                author_id = comment.author.id
                author_type_mapping[comment.author.type].add(author_id)
            for reply in comment.replies:
                author_id = reply.author.id
                reply_to_id = reply.reply_to.id
                author_type_mapping[reply.author.type].add(author_id)
                author_type_mapping[reply.reply_to.type].add(reply_to_id)
    return {"users_ids": users_ids, "groups_ids": groups_ids}


def add_authors_names(posts: list[Post], authors_ids: dict) -> list[Post]:

    id_to_name = {}
    users_to_fetch = authors_ids["users_ids"]
    groups_to_fetch = authors_ids["groups_ids"]

    if users_to_fetch:
        users = vk_api.get_users_names(users_to_fetch)
        id_to_name.update(users)
        update_user_names_cache(users)

    if groups_to_fetch:
        groups = vk_api.get_groups_names(groups_to_fetch)
        id_to_name.update(groups)
        update_group_names_cache(groups)

    posts_with_names = posts
    for post in posts:
        for comment in post.comments:
            if not comment.author.name:
                comment.author.name = id_to_name.get(
                    comment.author.id, "Неизвестный автор"
                )
            for reply in comment.replies:
                if not reply.author.name:
                    reply.author.name = id_to_name.get(
                        reply.author.id, "Неизвестный автор"
                    )
                if not reply.reply_to.name:
                    reply.reply_to.name = id_to_name.get(
                        reply.reply_to.id, "Неизвестный автор"
                    )
    return posts_with_names


def make_author(uid):
    if uid < 0:
        return Author(
            id=abs(uid), name=cache.get_group_name(uid), type="group"
        )
    return Author(id=abs(uid), name=cache.get_user_name(uid), type="user")


def update_user_names_cache(users):
    for user_id, user_name in users.items():
        cache.save_user_name(user_id, user_name)


def update_group_names_cache(groups):
    for group_id, group_name in groups.items():
        cache.save_group_name(group_id, group_name)
