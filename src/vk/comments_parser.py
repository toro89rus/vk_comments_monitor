import re
from datetime import date, datetime, timedelta

import src.cache as cache
import src.vk.api as vk_api
from src.logger import logger
from src.vk.classes import Author, Comment, Group, Post, Reply, User

logger = logger.getChild(__name__)


def get_new_comments() -> list[Post]:
    logger.info("Started new comments collecting")
    recent_posts = get_recent_posts_with_comments()
    posts_with_new_comments = []
    for post in recent_posts:
        if post_new_comments := collect_new_comments_for_post(post):
            posts_with_new_comments.append(post_new_comments)
    if posts_with_new_comments:
        users_ids, groups_ids = collect_author_ids(posts_with_new_comments)
        posts_with_new_comments = add_authors_names(
            posts_with_new_comments, users_ids, groups_ids
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


def collect_new_comments_for_post(post) -> Post:
    post_id = post["id"]
    post_text = f"{post['text'][:100]}..."
    post_date = date.fromtimestamp(post["date"])
    post_new_comments = []
    post_comments = vk_api.get_comments(post_id)
    for comment in post_comments:
        comment_id = comment["id"]
        thread_comment_id = int(
            cache.load_thread_comment_id(post_id, comment_id) or -1
        )
        if thread_comment_id == -1:
            serialized_comment = serialize_comment(comment)
            if serialized_comment:
                post_new_comments.append(Comment(**serialized_comment))
            cache.save_thread_comment_id(post_id, comment_id, 0)
        if comment["thread"]["count"] > 0:
            new_replies = collect_new_replies(
                comment["thread"], comment_id, thread_comment_id
            )
            if new_replies:
                post_new_comments.extend(new_replies)
                last_thread_comment = new_replies[-1]
                cache.save_thread_comment_id(
                    post_id, comment_id, last_thread_comment.id
                )
    if post_new_comments:
        logger.info(
            f"Collected post with {len(post_new_comments)} new comments"
        )
        return Post(
            id=post_id,
            created_at=post_date,
            text=post_text,
            comments=post_new_comments,
        )

    return None


def serialize_comment(vk_comment: dict) -> Comment | None:
	comment_text = format_comment_text(vk_comment["text"])
    if not comment_text:
        return None
    author_name = cache.load_user_name(vk_comment["from_id"])
    return {
        "id": vk_comment["id"],
        "created_at": datetime.fromtimestamp(vk_comment["date"]),
        "author": Author(vk_comment["from_id"], author_name),
        "text": comment_text,
    }
    
def serialize_reply(comment_id, reply):
	comment_text = format_reply_text(vk_comment["text"])
	reply_to_id = vk_comment["reply_to_user"]
    reply_to_name = cache.load_user_name(reply_to_id)
    reply_to = Author(reply_to_id, reply_to_name)
    reply_on = comment_id
    return {
        "id": vk_comment["id"],
        "created_at": datetime.fromtimestamp(vk_comment["date"]),
        "author": Author(vk_comment["from_id"], author_name),
        "text": comment_text,
        "reply_to": reply_to
        "reply_on": comment_id
    }


def collect_new_replies(
	thread, comment_id, thread_last_comment_id: int) 
	-> list[Reply]:
    new_replies = []
    thread_replies = thread["items"]
    for reply in thread_replies:
        if reply["id"] > thread_last_comment_id:
            serialized_reply = serialize_reply(comment_id, reply)
            if serialized_reply:
                new_replies.append(Reply(**serialized_reply))
        else:
            break
    return new_replies


def collect_author_ids(posts: list[Post]) -> tuple[set]:
    users_ids, groups_ids = set(), set()
    for post in posts:
        for comment in post.comments:
            author_id = comment.author.id
            if isinstance(comment.author, User):
                users_ids.add(author_id)
            elif isinstance(comment.author, Group):
                groups_ids.add(author_id)
    return users_ids, groups_ids


def add_authors_names(
    posts: list[Post], users_ids: set, groups_ids: set
) -> list[Post]:

    id_to_name, users_to_fetch, groups_to_fetch = get_cached_user_names(
        users_ids, groups_ids
    )

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
            comment.author.name = id_to_name.get(
                comment.author.id, "Неизвестный автор"
            )
    return posts_with_names


def get_cached_user_names(
    users_ids: set, groups_ids: set
) -> tuple[dict, list, list]:

    cached_names = {}
    remaining_users, remaining_groups = set(users_ids), set(groups_ids)

    for group_id in groups_ids:
        cached_name = cache.load_group_name(group_id)
        if cached_name:
            cached_names[group_id] = cached_name
            remaining_groups.discard(group_id)

    for user_id in users_ids:
        cached_name = cache.load_user_name(user_id)
        if cached_name:
            cached_names[user_id] = cached_name
            remaining_users.discard(user_id)

    return cached_names, list(remaining_users), list(remaining_groups)


def update_user_names_cache(users):
    for user_id, user_name in users.items():
        cache.save_user_name(user_id, user_name)


def update_group_names_cache(groups):
    for group_id, group_name in groups.items():
        cache.save_group_name(group_id, group_name)


def format_reply_text(reply_text):
    if not reply_text:
        return None
    match = re.search(r"\[(?:id|club)\d+\|([^\]]+)], (.*)", reply_text)
    if not match:
        return reply_text if is_valid_text(reply_text) else None
    name, text = match.groups()
    return f"{name}, {text}" if is_valid_text(text) else None


def format_comment_text(comment_text):
    if not comment_text:
        return None
    return comment_text if is_valid_text(comment_text) else None


def is_valid_text(text):
    stripped_text = re.sub(r"[^\u0400-\u04FFa-zA-Z]+", "", text)
    if not stripped_text:
        return False
    return stripped_text.lower() != "спасибо"
