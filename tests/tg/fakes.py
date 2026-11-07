"""Подмены aiogram-объектов для тестов: бот и входящее сообщение."""

from dataclasses import dataclass, field

from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from aiogram.types import User


@dataclass
class SentMessage:
    chat_id: int
    text: str
    reply_markup: object = None
    parse_mode: str | None = None


class FakeBot:
    """Запоминает отправленные сообщения. Чатам из blocked_by отвечает
    TelegramForbiddenError, чатам из errors — заданным исключением на каждую
    отправку, чатам из pending_errors — исключениями из списка по одному на
    отправку, пока список не кончится."""

    def __init__(self):
        self.sent: list[SentMessage] = []
        self.blocked_by: set[int] = set()
        self.errors: dict[int, Exception] = {}
        self.pending_errors: dict[int, list[Exception]] = {}

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: object = None,
        parse_mode: str | None = None,
    ) -> None:
        if chat_id in self.blocked_by:
            raise TelegramForbiddenError(
                method=SendMessage(chat_id=chat_id, text=text),
                message="Forbidden: bot was blocked by the user",
            )
        if chat_id in self.errors:
            raise self.errors[chat_id]
        if self.pending_errors.get(chat_id):
            raise self.pending_errors[chat_id].pop(0)
        self.sent.append(SentMessage(chat_id, text, reply_markup, parse_mode))

    def texts_for(self, chat_id: int) -> list[str]:
        return [m.text for m in self.sent if m.chat_id == chat_id]


@dataclass
class FakeMessage:
    """Входящее сообщение: from_user и ответы через answer()."""

    from_user: User
    text: str = ""
    answers: list[SentMessage] = field(default_factory=list)

    async def answer(self, text: str, reply_markup: object = None) -> None:
        self.answers.append(SentMessage(self.from_user.id, text, reply_markup))


def tg_user(user_id: int, first_name: str = "Иван") -> User:
    return User(
        id=user_id,
        is_bot=False,
        first_name=first_name,
        last_name="Петров",
        username=f"user{user_id}",
    )
