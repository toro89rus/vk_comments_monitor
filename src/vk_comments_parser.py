from datetime import date, datetime, timedelta

import vk_api

from config.settings import VK_GROUP_ID, VK_TOKEN
from src.logger import logger

logger = logger.getChild(__name__)


def get_new_comments(latest_saved_posts, group_id=VK_GROUP_ID, days=7):
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    new_comments = []
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    posts = vk.wall.get(owner_id=group_id, count=20, sort="desc", filter="all")[
        "items"
    ]
    logger.info("Loaded posts")
    for post in posts:
        post_date = date.fromtimestamp(post["date"])
        if post["comments"]["count"] > 0 and post_date >= start_date:
            post_id = post["id"]
            post_text = f"{post["text"][:100]}..."
            if str(post_id) in latest_saved_posts:
                latest_saved_comment_id = latest_saved_posts[str(post_id)][
                    "comment_id"
                ]
            else:
                latest_saved_comment_id = None
            comments = vk.wall.getComments(
                owner_id=group_id, post_id=post_id, count=100
            )["items"]
            post_new_comments = []
            for comment in comments:
                comment_text = comment["text"]
                comment_id = comment["id"]
                if comment_text and (
                    not latest_saved_comment_id
                    or comment_id > latest_saved_comment_id
                ):
                    comment_author_id = comment["from_id"]
                    if comment_author_id < 0:
                        comment_author_name = vk.groups.getById(
                            group_id=abs(comment_author_id)
                        )[0]["name"]
                    else:
                        comment_author = vk.users.get(
                            user_ids=comment_author_id
                        )[0]
                        comment_author_first_name = comment_author.get(
                            "first_name"
                        )
                        comment_author_last_name = comment_author.get(
                            "last_name"
                        )
                        comment_author_name = f"{comment_author_first_name} {comment_author_last_name}"

                    comment_time = datetime.fromtimestamp(comment["date"])
                    post_new_comments.append(
                        {
                            "comment_id": comment_id,
                            "comment_time": comment_time,
                            "text": comment_text,
                            "author": comment_author_name,
                            "author_id": comment_author_id,
                        }
                    )
            if post_new_comments:
                new_comments.append(
                    {
                        "post_id": post_id,
                        "post_date": post_date,
                        "post_text": post_text,
                        "new_comments": post_new_comments,
                    }
                )
            #logger.info(f"Post {post_id} parsed")
    logger.info("Comments parsed")
    return new_comments


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
