from tatd_bot.vk.models import Post, Comment, Reply
from tatd_bot.config.settings import VK_GROUP_LINK
from datetime import datetime
from tatd_bot.config.settings import DATETIME_FORMAT, DATE_FORMAT


def _format_date(timestamp: datetime):
    return timestamp.date().strftime(DATE_FORMAT)


def _format_datetime(timestamp: datetime):
    return timestamp.replace(tzinfo=None).strftime(DATETIME_FORMAT)


def format_post(post: Post) -> str:
    shortened_text = f"{post.text[:100]}..."
    link_tag = f"<a href='{VK_GROUP_LINK}_{post.id}'>Пост</a>"
    return f"{link_tag} от {_format_date(post.created_at)}\n{shortened_text}"


def format_comment(comment: Comment) -> str:
    return (
        f"{comment.created_at}\n"
        f"Комментарий от {comment.author.name_gen}\n"
        f"{comment.text}"
    )


def format_reply(reply: Reply) -> str:
    return (
        f"{_format_datetime(reply.created_at)}\n"
        f"Ответ для {reply.reply_to.name_gen} от {reply.author.name_gen} \n"
        f"{reply.text}"
    )
