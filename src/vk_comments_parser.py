from datetime import date, datetime, timedelta

import vk_api
from vk_api.exceptions import VkApiError

from config.settings import VK_GROUP_ID, VK_TOKEN
from src.logger import logger

logger = logger.getChild(__name__)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()


def main(latest_saved_posts):
    logger.info("Started new comments collecting")
    recent_posts = get_recent_posts_with_comments()
    new_comments = []
    for post in recent_posts:
        post_new_comments = collect_new_comments_for_post(
            post, latest_saved_posts
        )
        if post_new_comments:
            new_comments.append(post_new_comments)
    logger.info(f"Collected {len(new_comments)} posts with new comments")
    return new_comments


def safe_vk_call(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except VkApiError as exc:
        logger.error(f"VK Api Error: {exc} for {method} with {args, kwargs}")
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}.Traceback -", exc_info=True)
    return None


def get_recent_posts_with_comments(
    group_id: int = VK_GROUP_ID, days: int = 7
) -> list:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    posts_response = safe_vk_call(vk.wall.get, owner_id=group_id, count=20)
    if not posts_response:
        return []
    posts = posts_response["items"]
    recent_posts_with_comments = []
    for post in posts:
        post_date = date.fromtimestamp(post["date"])
        has_comments = post["comments"]["count"] > 0
        if has_comments and post_date >= start_date:
            recent_posts_with_comments.append(post)
    return recent_posts_with_comments


def collect_new_comments_for_post(
    post, latest_saved_posts, group_id=VK_GROUP_ID
):
    post_id = post["id"]
    post_text = f"{post["text"][:100]}..."
    post_date = date.fromtimestamp(post["date"])
    post_new_comments = []
    if str(post_id) in latest_saved_posts:
        last_saved_comment_id = latest_saved_posts[str(post_id)]["comment_id"]
    else:
        last_saved_comment_id = 0
    post_comments_response = safe_vk_call(
        vk.wall.getComments,
        owner_id=group_id,
        post_id=post_id,
        count=100,
        sort="asc",
        start_comment_id=last_saved_comment_id,
    )
    if not post_comments_response:
        return []
    post_comments = post_comments_response["items"]
    for post_comment in post_comments:
        print(post_comment["id"])
        new_comment = process_comment(post_comment)
        if new_comment:
            post_new_comments.append(new_comment)
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


def process_comment(comment):
    comment_text = comment["text"]
    if comment_text:
        comment_author = get_author(comment["from_id"])
        comment_time = datetime.fromtimestamp(comment["date"])
        return {
            "comment_id": comment["id"],
            "comment_time": comment_time,
            "text": comment_text,
            "author": comment_author,
            "author_id": comment["from_id"],
        }


def get_author(author_id):
    if author_id < 0:
        group_id = abs(author_id)
        group_response = safe_vk_call(vk.groups.getById, group_id=group_id)
        if not group_response:
            return "Неизвестное сообщество"
        return group_response[0]["name"]

    users_response = safe_vk_call(vk.users.get, user_ids=author_id)
    if not users_response:
        return "Неизвестный автор"
    user = users_response[0]
    first_name = user.get("first_name")
    last_name = user.get("last_name")
    return f"{first_name} {last_name}"


def update_latest_comments(latest_saved_posts, new_comments):
    logger.info("Started latest_comments update")
    for post_with_new_comments in new_comments:
        post_id = post_with_new_comments["post_id"]
        latest_new_comment_id = post_with_new_comments["new_comments"][-1][
            "comment_id"
        ]
        if post_id in latest_saved_posts:
            latest_saved_posts[post_id]["comment_id"] = latest_new_comment_id
        else:
            latest_saved_posts[post_id] = {"comment_id": latest_new_comment_id}
    logger.info("Finished latest_comments update")
    return latest_saved_posts
