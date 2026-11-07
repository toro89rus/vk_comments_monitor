from datetime import datetime

import pytest
from petrovich.enums import Gender

from tatd_bot.tg.formatters import TgMessageFormatter
from tatd_bot.vk.models import Comment, Group, Post, Reply, User

CREATED_AT = datetime(2026, 3, 5, 9, 7)
IVAN = User(1, "Иван", "Петров", Gender.MALE)
MARIA = User(2, "Мария", "Иванова", Gender.FEMALE)


@pytest.fixture
def formatter(app_config):
    return TgMessageFormatter(app_config)


def make_post(text: str) -> Post:
    return Post(id=42, created_at=CREATED_AT, text=text, comments=[])


def test_format_post(formatter):
    assert formatter.format_post(make_post("Премьера")) == (
        "<a href='https://vk.com/tuldramteatr?w=wall-48164678_42'>Пост</a>"
        " от 05.03.2026\n"
        "Премьера..."
    )


def test_format_post_shortens_text_to_100_chars(formatter):
    result = formatter.format_post(make_post("а" * 150))

    assert result.endswith("\n" + "а" * 100 + "...")


def test_format_post_escapes_html(formatter):
    result = formatter.format_post(make_post("<b>Tom & Jerry</b>"))

    assert result.endswith("\n&lt;b&gt;Tom &amp; Jerry&lt;/b&gt;...")


def test_format_comment(formatter):
    comment = Comment(
        id=1,
        created_at=CREATED_AT,
        author=IVAN,
        text="Отлично",
        replies=[],
        is_new=True,
    )

    assert formatter.format_comment(comment) == (
        "05.03.2026 09:07\nКомментарий от Ивана Петрова\n\nОтлично"
    )


def test_format_comment_keeps_text_as_is(formatter):
    comment = Comment(1, CREATED_AT, IVAN, "<b>Tom & Jerry</b>", [], True)

    assert formatter.format_comment(comment).endswith("\n\n<b>Tom & Jerry</b>")


def test_format_reply_keeps_text_as_is(formatter):
    reply = Reply(2, CREATED_AT, MARIA, "Tom & Jerry", IVAN)

    assert formatter.format_reply(reply).endswith("\n\nTom & Jerry")


@pytest.mark.parametrize(
    ("author", "expected_name"),
    [
        (Group(5, "Театр"), "Театр"),
        (User(9), "неизвестного пользователя"),
        (Group(5), "неизвестной группы"),
    ],
)
def test_format_comment_author_name(formatter, author, expected_name):
    comment = Comment(1, CREATED_AT, author, "Отлично", [], True)

    assert f"Комментарий от {expected_name}\n" in formatter.format_comment(
        comment
    )


def test_format_reply(formatter):
    reply = Reply(
        id=2,
        created_at=CREATED_AT,
        author=MARIA,
        text="Согласна",
        reply_to=IVAN,
    )

    assert formatter.format_reply(reply) == (
        "05.03.2026 09:07\n"
        "Ответ для Ивана Петрова от Марии Ивановой \n\n"
        "Согласна"
    )


def test_format_reply_to_unknown_user(formatter):
    reply = Reply(2, CREATED_AT, MARIA, "Согласна", User(0))

    assert "Ответ для неизвестного пользователя от Марии Ивановой" in (
        formatter.format_reply(reply)
    )
