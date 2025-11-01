from datetime import date, datetime, timedelta

import vk_api

from config.settings import VK_GROUP_ID, VK_TOKEN
from src.logger import logger

logger = logger.getChild(__name__)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()


def main(latest_saved_posts):
    recent_posts = get_recent_posts()
    new_comments = []
    for post in recent_posts:
        post_new_comments = get_post_new_comments(post, latest_saved_posts)
        if post_new_comments:
            new_comments.append(post_new_comments)
    return new_comments


def get_recent_posts(group_id: int = VK_GROUP_ID, days: int = 7) -> list:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    posts = vk.wall.get(owner_id=group_id, count=20, sort="desc", filter="all")[
        "items"
    ]
    recent_posts = []
    for post in posts:
        post_date = date.fromtimestamp(post["date"])
        if post["comments"]["count"] > 0 and post_date >= start_date:
            recent_posts.append(post)
    return recent_posts


def get_post_new_comments(post, latest_saved_posts, group_id=VK_GROUP_ID):
    post_id = post["id"]
    post_text = f"{post["text"][:100]}..."
    post_date = date.fromtimestamp(post["date"])
    post_comments = vk.wall.getComments(
        owner_id=group_id, post_id=post_id, count=100
    )["items"]
    post_new_comments = []
    if str(post_id) in latest_saved_posts:
        last_saved_comment_id = latest_saved_posts[str(post_id)]["comment_id"]
    else:
        last_saved_comment_id = 0
    for post_comment in post_comments:
        new_comment = process_comment(last_saved_comment_id, post_comment)
        if new_comment:
            post_new_comments.append(new_comment)
    if post_new_comments:
        return {
            "post_id": post_id,
            "post_date": post_date,
            "post_text": post_text,
            "new_comments": post_new_comments,
        }


def process_comment(last_saved_comment_id, comment):
    comment_text = comment["text"]
    comment_id = comment["id"]
    if comment_text and comment_id > last_saved_comment_id:
        comment_author_id = comment["from_id"]
        comment_author = get_author(comment_author_id)
        comment_time = datetime.fromtimestamp(comment["date"])
        return {
            "comment_id": comment_id,
            "comment_time": comment_time,
            "text": comment_text,
            "author": comment_author,
            "author_id": comment_author_id,
        }


def get_author(author_id):
    if author_id < 0:
        group_id = abs(author_id)
        return vk.groups.getById(group_id=group_id)[0]["name"]
    author = vk.users.get(user_ids=author_id)[0]
    first_name = author.get("first_name")
    last_name = author.get("last_name")
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
