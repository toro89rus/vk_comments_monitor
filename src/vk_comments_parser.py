from datetime import date, datetime, timedelta

import src.vk as vk
import src.cache as cache
from src.logger import logger


logger = logger.getChild(__name__)


redis_key_name = "post:{post_id}:comment:{comment_id}:thread_comment_id"


def get_new_comments():
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
    posts = vk.get_posts()
    recent_posts_with_comments = []
    for post in posts:
        post_date = date.fromtimestamp(post["date"])
        has_comments = post["comments"]["count"] > 0
        if has_comments and post_date >= start_date:
            recent_posts_with_comments.append(post)
    return recent_posts_with_comments


def collect_new_comments_for_post(post):
    post_id = post["id"]
    post_text = f"{post['text'][:100]}..."
    post_date = date.fromtimestamp(post["date"])
    post_new_comments = []
    post_comments = vk.get_comments(post_id)
    for comment in post_comments:
        comment_id = comment["id"]
        thread_comment_id = cache.load_thread_comment_id(post_id, comment_id)
        if thread_comment_id == -1:
            new_comment = serialize_comment(comment)
            if new_comment:
                post_new_comments.append(new_comment)
            cache.save_thread_comment_id(post_id, comment_id, 0)
        if comment["thread"]["count"] > 0:
            new_thread_comments = collect_new_thread_comments(
                comment["thread"], thread_comment_id
            )
            if new_thread_comments:
                post_new_comments.extend(new_thread_comments)
                last_thread_comment_id = new_thread_comments[-1]["id"]
                cache.save_thread_comment_id(
                    post_id, comment_id, last_thread_comment_id
                )
    if post_new_comments:
        logger.info(
            f"Collected post with {len(post_new_comments)} new comments"
        )
        return {
            "post_id": post_id,
            "post_date": post_date,
            "post_text": post_text,
            "new_comments": post_new_comments,
        }
    return None


def serialize_comment(comment):
    # to-do process text - exclude "спасибо" only text
    comment_text = comment["text"]
    if not comment_text:
        return None
    comment_time = datetime.fromtimestamp(comment["date"])

    result = {
        "id": comment["id"],
        "created_at_date": comment_time,
        "text": comment_text,
        "author_id": comment["from_id"],
    }
    if comment.get("reply_to_comment"):
        result["reply_to"] = comment["reply_to_user"]

    return result


def collect_new_thread_comments(thread, thread_last_comment_id):
    new_thread_comments = []
    thread_comments = thread["items"]
    for thread_comment in thread_comments:
        if thread_comment["id"] > thread_last_comment_id:
            processed_thread_comment = serialize_comment(thread_comment)
            if processed_thread_comment:
                new_thread_comments.append(processed_thread_comment)
        else:
            break
    return new_thread_comments


def collect_author_ids(new_comments):
    users_ids, groups_ids = set(), set()
    for post in new_comments:
        for comment in post["new_comments"]:
            author_id = comment["author_id"]
            if author_id > 0:
                users_ids.add(author_id)
            else:
                groups_ids.add(abs(author_id))
    return users_ids, groups_ids


def add_authors_names(posts, users_ids, groups_ids):

    id_to_name, users_to_fetch, groups_to_fetch = get_cached_user_names(
        users_ids, groups_ids
    )

    if users_to_fetch:
        users = vk.get_users_names(users_to_fetch)
        id_to_name.update(users)
        update_user_names_cache(users)

    if groups_to_fetch:
        groups = vk.get_groups_names(groups_to_fetch)
        id_to_name.update(groups)
        update_group_names_cache(groups)

    posts_with_names = posts
    for post in posts:
        for comment in post["new_comments"]:
            comment["author_name"] = id_to_name.get(
                comment["author_id"], "Неизвестный автор"
            )
    return posts_with_names


def get_cached_user_names(users_ids, groups_ids):

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

