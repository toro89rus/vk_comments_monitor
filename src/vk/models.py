from dataclasses import dataclass
from datetime import date, datetime
from typing import ClassVar, Optional

from petrovich.enums import Case, Gender
from petrovich.main import Petrovich

from config.settings import VK_GROUP_LINK

p = Petrovich()


@dataclass
class Group:
    id: int
    name: Optional[str] = None

    kind: ClassVar[str] = "group"

    def __str__(self):
        if self.name:
            return self.name
        return "Неизвестная группа"

    # Родительный
    @property
    def name_gen(self):
        return self.name

    # Дательный
    @property
    def name_dat(self):
        return self.name

    def update(self, data: dict) -> None:
        if data.get("name"):
            self.name = data["name"]


@dataclass
class User:
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None

    kind: ClassVar[str] = "user"

    def _in_case(self, case: Case):
        if not self.first_name or not self.last_name or not self.gender:
            return self.name
        first = p.firstname(self.first_name, case, self.gender)
        last = p.lastname(self.last_name, case, self.gender)
        return f"{first} {last}"

    @property
    def name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return None

    def __str__(self):
        if self.first_name and self.last_name:
            return self.name
        return "Неизвестный пользователь"

    def update(self, data: dict) -> None:
        for field in ("first_name", "last_name", "gender"):
            value = data.get(field)
            if value:
                setattr(self, field, value)

    # Родительный
    @property
    def name_gen(self):
        return self._in_case(Case.GENITIVE)

    # Дательный
    @property
    def name_dat(self):
        return self._in_case(Case.DATIVE)


@dataclass
class Reply:
    id: int
    created_at: datetime
    author: User | Group
    text: str
    reply_to: User | Group

    def __str__(self) -> str:
        return (
            f"{self.created_at}\n"
            f"Ответ для {self.reply_to.name_gen} от {self.author.name_gen} \n"
            f"{self.text}"
        )


@dataclass
class Comment:
    id: int
    created_at: datetime
    author: User | Group
    text: str
    replies: list[Reply]
    is_new: Optional[bool] = None

    def __str__(self) -> str:
        return (
            f"{self.created_at}\n"
            f"Комментарий от {self.author.name_gen}\n"
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
