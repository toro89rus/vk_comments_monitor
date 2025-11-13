from dataclasses import dataclass
from datetime import date, datetime

from config.settings import VK_GROUP_LINK
import src.cache as cache


class Author:

    def __new__(cls, id: int, name: str = None):
        if cls is Author:
            if id > 0:
                return super().__new__(User)
            else:
                return super().__new__(Group)
        return super().__new__(cls)

    def __init__(self, id: int, name: str | None = None):
        self.id: int = abs(id)
        self.name: str | None = name

    def __str__(self):
        if self.name:
            return self.name
        return "Имя автора неизвестно"


class User(Author):
    pass


class Group(Author):
    pass


@dataclass
class Comment:
    id: int
    created_at: datetime
    author: User | Group
    text: str

    def __str__(self):
        return (
            f"Комментарий от {self.author.name} {self.created_at}"
            f"\n{self.text}"
        )


@dataclass
class Reply(Comment):
    reply_to: User | Group

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
