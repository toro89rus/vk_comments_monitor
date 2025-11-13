from dataclasses import dataclass
from datetime import date, datetime

from config.settings import VK_GROUP_LINK
import src.cache as cache


class Author:

    def __new__(cls, id, name=""):
        if cls is Author:
            if id > 0:
                return super().__new__(User)
            else:
                return super().__new__(Group)
        return super().__new__(cls)

    def __init__(self, id: int, name: str = ""):
        self.id: int = abs(id)
        if not name:
            if id < 0:
                name = cache.load_user_name(id) or ""
            else:
                name = cache.load_group_name(id) or ""
        self._name = name

    def __str__(self):
        return self.name


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
    reply_to: int = None

    def __str__(self):
        if self.reply_to:
            comment_type = "Ответ на комментарий"
        else:
            comment_type = "Комментарий"
        return (
            f"{comment_type} от {self.author.name} {self.created_at}"
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
