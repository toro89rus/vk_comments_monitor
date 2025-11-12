from dataclasses import dataclass
from datetime import date, datetime

from config.settings import VK_GROUP_LINK


@dataclass
class Author:
    id: int

    @staticmethod
    def from_id(author_id: int) -> "User | Group":
        if author_id > 0:
            return User(id=author_id)
        else:
            return Group(id=abs(author_id))


@dataclass
class User(Author):
    id: int
    name: str = ""

    def __str__(self):
        return self.name


@dataclass
class Group(Author):
    id: int
    name: str = ""

    def __str__(self):
        return self.name


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
