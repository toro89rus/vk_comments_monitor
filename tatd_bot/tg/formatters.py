import html
from datetime import datetime

from tatd_bot.config import AppConfig
from tatd_bot.vk.models import Comment, Post, Reply


class TgMessageFormatter:

    def __init__(self, config: AppConfig):
        self.config = config

    def _format_date(self, timestamp: datetime):
        return timestamp.date().strftime(self.config.date_format)

    def _format_datetime(self, timestamp: datetime):
        return timestamp.strftime(self.config.datetime_format)

    def format_post(self, post: Post) -> str:
        shortened_text = f"{html.escape(post.text[:100])}..."
        link_tag = f"<a href='{self.config.vk.group_link}_{post.id}'>Пост</a>"
        formatted_date = self._format_date(post.created_at)
        return f"{link_tag} от {formatted_date}\n{shortened_text}"

    def format_comment(self, comment: Comment) -> str:
        return (
            f"{self._format_datetime(comment.created_at)}\n"
            f"Комментарий от {comment.author.name_gen}\n\n"
            f"{html.escape(comment.text)}"
        )

    def format_reply(self, reply: Reply) -> str:
        author_name = reply.author.name_gen
        reply_to_name = reply.reply_to.name_gen
        return (
            f"{self._format_datetime(reply.created_at)}\n"
            f"Ответ для {reply_to_name} от {author_name} \n\n"
            f"{html.escape(reply.text)}"
        )
