from dataclasses import dataclass
from datetime import date, datetime
from typing import ClassVar, Optional

from petrovich.enums import Case, Gender
from petrovich.main import Petrovich

p = Petrovich()


@dataclass
class Group:
    id: int
    name: Optional[str] = None

    kind: ClassVar[str] = "group"
    cache: ClassVar[dict] = {}

    def __str__(self):
        if self.name:
            return self.name
        return "Неизвестная группа"

    @classmethod
    def get_existing(cls, gid: int) -> "Group":
        if gid in cls.cache:
            return cls.cache[gid]
        None

    @classmethod
    def register(cls, group: "Group") -> "Group":
        cls.cache[group.id] = group

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
    # has_full_name: bool = False ?

    kind: ClassVar[str] = "user"
    cache: ClassVar[dict] = {}

    @classmethod
    def get_existing(cls, uid: int) -> "User":
        if uid in cls.cache:
            return cls.cache[uid]
        None

    @classmethod
    def register(cls, user: "User") -> "User":
        cls.cache[user.id] = user

    def _in_case(self, case: Case):
        if not all((self.first_name, self.last_name, self.gender)):
            return self.name
        first = p.firstname(self.first_name, case, self.gender)
        last = p.lastname(self.last_name, case, self.gender)
        return f"{first} {last}"

    @property
    def name(self):
        # if self.name: return self.name ???
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
    created_at: date
    text: str
    comments: list[Comment]
