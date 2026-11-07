from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Optional

from petrovich.enums import Case
from petrovich.main import Petrovich

p = Petrovich()

# Как назвать автора без имени в тексте сообщения
UNKNOWN_GROUP_GEN = "неизвестной группы"
UNKNOWN_GROUP_DAT = "неизвестной группе"
UNKNOWN_USER_GEN = "неизвестного пользователя"
UNKNOWN_USER_DAT = "неизвестному пользователю"


@dataclass
class Group:
    id: int
    name: str | None = None

    kind: ClassVar[str] = "group"

    def __str__(self):
        if self.name:
            return self.name
        return "Неизвестная группа"

    # Родительный
    @property
    def name_gen(self) -> str:
        return self.name or UNKNOWN_GROUP_GEN

    # Дательный
    @property
    def name_dat(self) -> str:
        return self.name or UNKNOWN_GROUP_DAT

    def update(self, data: dict) -> None:
        if data.get("name"):
            self.name = data["name"]


@dataclass
class User:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None

    kind: ClassVar[str] = "user"

    def _in_case(self, case: Case):
        if not all((self.first_name, self.last_name, self.gender)):
            return self.name
        try:
            first = p.firstname(self.first_name, case, self.gender)
            last = p.lastname(self.last_name, case, self.gender)
            return f"{first} {last}"
        except Exception:  # noqa: BLE001
            return self.name

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
    def name_gen(self) -> str:
        return self._in_case(Case.GENITIVE) or UNKNOWN_USER_GEN

    # Дательный
    @property
    def name_dat(self) -> str:
        return self._in_case(Case.DATIVE) or UNKNOWN_USER_DAT


@dataclass
class Reply:
    id: int
    created_at: datetime
    author: User | Group
    text: str
    reply_to: User | Group


@dataclass
class Comment:
    id: int
    created_at: datetime
    author: User | Group
    text: str
    replies: list[Reply]
    is_new: Optional[bool] = None

    def has_new_activity(self) -> bool:
        if self.is_new and self.text:
            return True
        if self.replies:
            return True
        return False


@dataclass
class Post:
    id: int
    created_at: datetime
    text: str
    comments: list[Comment]
