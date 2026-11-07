from dataclasses import dataclass
from enum import Enum


class BotUserStatus(Enum):
    PENDING = "pending"
    SUBSCRIBED = "subscribed"
    REJECTED = "rejected"
    UNSUBSCRIBED = "unsubscribed"
    NEW = "new"


@dataclass
class BotUser:
    id: int
    full_name: str
    username: str | None
    status: BotUserStatus
