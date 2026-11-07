from datetime import datetime

import pytest
from petrovich.enums import Gender

from tatd_bot.vk.models import Comment, Group, Reply, User

CREATED_AT = datetime(2026, 1, 1, 12, 0)


class TestUser:
    def test_full_name(self):
        user = User(1, "Иван", "Петров", Gender.MALE)

        assert user.name == "Иван Петров"
        assert str(user) == "Иван Петров"

    def test_male_name_declension(self):
        user = User(1, "Иван", "Петров", Gender.MALE)

        assert user.name_gen == "Ивана Петрова"
        assert user.name_dat == "Ивану Петрову"

    def test_female_name_declension_with_gender_as_string(self):
        # в Redis пол хранится строкой
        user = User(1, "Мария", "Иванова", "female")

        assert user.name_gen == "Марии Ивановой"
        assert user.name_dat == "Марии Ивановой"

    @pytest.mark.parametrize("gender", [None, "", "unknown"])
    def test_name_without_known_gender_is_not_declined(self, gender):
        user = User(1, "Иван", "Петров", gender)

        assert user.name_gen == "Иван Петров"

    def test_unknown_user(self):
        user = User(1)

        assert user.name is None
        assert str(user) == "Неизвестный пользователь"
        assert user.name_gen == "неизвестного пользователя"
        assert user.name_dat == "неизвестному пользователю"

    def test_user_with_only_first_name_has_no_name(self):
        user = User(1, "Иван")

        assert user.name is None
        assert str(user) == "Неизвестный пользователь"
        assert user.name_gen == "неизвестного пользователя"

    def test_update_overwrites_only_non_empty_fields(self):
        user = User(1, "Иван", "Петров", Gender.MALE)

        user.update({"first_name": "Пётр", "last_name": "", "gender": None})

        assert (user.first_name, user.last_name, user.gender) == (
            "Пётр",
            "Петров",
            Gender.MALE,
        )


class TestGroup:
    def test_named_group_is_not_declined(self):
        group = Group(5, "Тульский театр драмы")

        assert str(group) == "Тульский театр драмы"
        assert group.name_gen == "Тульский театр драмы"
        assert group.name_dat == "Тульский театр драмы"

    def test_unknown_group(self):
        group = Group(5)

        assert str(group) == "Неизвестная группа"
        assert group.name_gen == "неизвестной группы"
        assert group.name_dat == "неизвестной группе"

    def test_update_ignores_empty_name(self):
        group = Group(5, "Театр")

        group.update({"name": ""})
        assert group.name == "Театр"

        group.update({"name": "Новый театр"})
        assert group.name == "Новый театр"


def make_reply() -> Reply:
    return Reply(
        id=2,
        created_at=CREATED_AT,
        author=User(1),
        text="ответ",
        reply_to=User(3),
    )


@pytest.mark.parametrize(
    ("is_new", "text", "replies", "expected"),
    [
        (True, "текст", [], True),
        (True, "", [], False),
        (False, "текст", [], False),
        (None, "текст", [], False),
        (False, "текст", [make_reply()], True),
        (True, "", [make_reply()], True),
    ],
)
def test_comment_has_new_activity(is_new, text, replies, expected):
    comment = Comment(
        id=1,
        created_at=CREATED_AT,
        author=User(1),
        text=text,
        replies=replies,
        is_new=is_new,
    )

    assert comment.has_new_activity() is expected
