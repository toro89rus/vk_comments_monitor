from datetime import timedelta

import pytest
from petrovich.enums import Gender

from tatd_bot.vk.mappers import (
    vk_to_post,
    vk_to_vk_group,
    vk_to_vk_user,
    vk_to_vk_user_base_data,
)
from tatd_bot.vk.models import Group, User

VK_USER = {"id": 1, "first_name": "Иван", "last_name": "Петров", "sex": 2}


@pytest.mark.parametrize(
    ("sex", "gender"),
    [(1, Gender.FEMALE), (2, Gender.MALE), (0, None)],
)
def test_vk_to_vk_user_maps_sex_to_gender(sex, gender):
    user = vk_to_vk_user({**VK_USER, "sex": sex})

    assert user == User(1, "Иван", "Петров", gender)


def test_vk_to_vk_user_base_data():
    assert vk_to_vk_user_base_data(VK_USER) == {
        "first_name": "Иван",
        "last_name": "Петров",
        "gender": Gender.MALE,
    }


@pytest.mark.parametrize(
    "vk_user",
    [
        # текущее поведение: без поля sex или с неизвестным значением — KeyError
        {"id": 1, "first_name": "Иван", "last_name": "Петров"},
        {**VK_USER, "sex": 3},
    ],
)
def test_vk_user_without_known_sex_raises(vk_user):
    with pytest.raises(KeyError):
        vk_to_vk_user_base_data(vk_user)


def test_vk_to_vk_group():
    assert vk_to_vk_group({"id": 5, "name": "Театр"}) == Group(5, "Театр")


def test_vk_to_post_converts_date_to_moscow_time():
    post = vk_to_post({"id": 10, "date": 0, "text": "текст"}, comments=[])

    assert post.id == 10
    assert post.text == "текст"
    assert post.comments == []
    assert post.created_at.utcoffset() == timedelta(hours=3)
    assert post.created_at.hour == 3
