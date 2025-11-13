 from dataclasses import dataclass
from datetime import date, datetime

from config.settings import VK_GROUP_LINK
import src.cache as cache


class Author:
    def __init__(self, id: int, name: str | None = None):
        self.id: int = abs(id)
        self.name: str | None = name
        if id < 0:
			self.id = abs(id)
			self.type = "group"
		else:
			self.id = id
			self.type = "user"

    def __str__(self):
        if self.name:
            return self.name
        return "Имя автора неизвестно"


@dataclass
class Comment:
    id: int
    created_at: datetime
    author: User | Group
    text: str
    replies = list[Reply]

    def __str__(self):
        return (
            f"Комментарий от {self.author.name} {self.created_at}"
            f"\n{self.text}"
        )


@dataclass
class Reply:
	id: int
    created_at: datetime
    author: User | Group
    text: str
    reply_to: User | Group
    reply_on: id

    def __str__(self):
        return (
            f"Ответ на комментарий от {self.author.name} {self.created_at}"
            f"\n{self.text}"
        )


@dataclass
class Post:
    id: int
    created_at: date
    text: str
    comments: list[Comment]

    def __str__(self):
        link_tag = f"<a href='{VK_GROUP_LINK}_{self.id}'>Пост</a>"
        return f"{link_tag} от {self.created_at}\n{self.text}"
