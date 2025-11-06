from datetime import date, datetime, timedelta

import vk
from src.logger import logger
from src.redis_setup import r

logger = logger.getChild(__name__)


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
    posts = vk.gqet_posts()
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
    last_comment_id = int(r.get(f"post:{post_id}:last_comment_id") or 0)
    post_comments = vk.get_comments(post_id, last_comment_id)
    for comment in post_comments:
        new_comment = process_comment(comment)
        if new_comment:
            post_new_comments.append(new_comment)
    if post_new_comments:
        logger.info(
            f"Collected post with {len(post_new_comments)} new comments"
        )
        last_comment_id = post_new_comments[-1]["comment_id"]
        r.set(f"post:{post_id}:last_comment_id", last_comment_id, ex=604800)
        return {
            "post_id": post_id,
            "post_date": post_date,
            "post_text": post_text,
            "new_comments": post_new_comments,
        }


def process_comment(comment):
    comment_text = comment["text"]
    if comment_text:
        comment_time = datetime.fromtimestamp(comment["date"])
        return {
            "comment_id": comment["id"],
            "comment_time": comment_time,
            "text": comment_text,
            "author_id": comment["from_id"],
        }


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
    id_to_name = {}

    if users_ids:
        users = vk.get_users_names(users_ids)
        id_to_name.update(users)

    if groups_ids:
        groups = vk.get_groups_names(groups_ids)
        id_to_name.update(groups)

    posts_with_names = posts
    for post in posts:
        for comment in post["new_comments"]:
            comment["author_name"] = id_to_name.get(
                comment["author_id"], "Неизвестный автор"
            )
    return posts_with_names


print(get_new_comments())
