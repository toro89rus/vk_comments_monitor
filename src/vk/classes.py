from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from config.settings import VK_GROUP_LINK


@dataclass
class Author:
    id: int
    type: str
    name: str | None = None

    def __str__(self):
        if self.name:
            return self.name
        return "Имя автора неизвестно"


@dataclass
class Reply:
    id: int
    created_at: datetime
    author: Author
    text: str
    reply_to: Author

    def __str__(self) -> str:
        return (
            f"{self.created_at}\n"
            f"Ответ для {self.reply_to.name} от {self.author.name} \n"
            f"{self.text}"
        )


@dataclass
class Comment:
    id: int
    created_at: datetime
    author: Author
    text: str
    replies: list[Reply]
    is_new: Optional[bool] = None

    def __str__(self) -> str:
        return (
            f"{self.created_at}\n"
            f"Комментарий от {self.author.name}\n"
            f"{self.text}"
        )

    def has_new_activity(self) -> bool:
        if self.is_new and self.text:
            return True
        if self.replies:
            return True
        return False


@dataclass
class Post:
    id: int
    created_at: date
    text: str
    comments: list[Comment]

    def __str__(self):
        link_tag = f"<a href='{VK_GROUP_LINK}_{self.id}'>Пост</a>"
        return f"{link_tag} от {self.created_at}\n{self.text}"
