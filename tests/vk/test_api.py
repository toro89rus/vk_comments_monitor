from unittest.mock import MagicMock, patch

import pytest
import requests

from tatd_bot.vk.api import VkApiService
from tests.vk.samples import (
    GROUP_ID,
    vk_comment,
    vk_group,
    vk_post,
    vk_user,
)

VK_URL = "https://api.vk.ru/method"


def vk_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def vk_error(code: int = 5, message: str = "User authorization failed"):
    return {
        "error": {
            "error_code": code,
            "error_msg": message,
            "request_params": [],
        }
    }


@pytest.fixture
def api(app_config):
    return VkApiService(app_config)


@pytest.fixture
def requests_get():
    with patch("tatd_bot.vk.api.requests.get") as get:
        get.return_value = vk_response({"response": {"items": []}})
        yield get


def call_params(requests_get) -> dict:
    return requests_get.call_args.kwargs["params"]


class TestRequest:
    def test_url_token_version_and_timeout(self, api, requests_get):
        api.get_posts()

        requests_get.assert_called_once()
        assert requests_get.call_args.args == (f"{VK_URL}/wall.get",)
        assert requests_get.call_args.kwargs["timeout"] == 10
        params = call_params(requests_get)
        assert params["access_token"] == "vk-test-token"
        assert params["v"] == "5.199"

    def test_list_params_are_joined_with_commas(self, api, requests_get):
        requests_get.return_value = vk_response({"response": []})

        api.get_users_names([1, 2, 3])

        params = call_params(requests_get)
        assert params["user_ids"] == "1,2,3"
        assert params["fields"] == "sex"

    @pytest.mark.parametrize(
        "error",
        [requests.ConnectionError("dns"), requests.Timeout("timeout")],
    )
    def test_network_error_returns_empty_result(
        self, api, requests_get, error, caplog
    ):
        requests_get.side_effect = error

        assert api.get_posts() == []
        assert "VK API network error while calling wall.get" in caplog.text

    def test_invalid_json_returns_empty_result(self, api, requests_get):
        requests_get.return_value.json.side_effect = ValueError("not json")

        assert api.get_posts() == []

    def test_vk_error_returns_empty_result_and_is_logged(
        self, api, requests_get, caplog
    ):
        requests_get.return_value = vk_response(vk_error())

        assert api.get_posts() == []
        assert "[5:None] User authorization failed" in caplog.text


class TestGetPosts:
    def test_request_params(self, api, requests_get):
        api.get_posts()

        params = call_params(requests_get)
        assert params["owner_id"] == str(GROUP_ID)
        assert params["count"] == 20

    def test_returns_items(self, api, requests_get):
        posts = [vk_post(1), vk_post(2)]
        requests_get.return_value = vk_response(
            {"response": {"count": 2, "items": posts}}
        )

        assert api.get_posts() == posts

    @pytest.mark.parametrize("payload", [{}, {"response": {}}])
    def test_response_without_items(self, api, requests_get, payload):
        requests_get.return_value = vk_response(payload)

        assert api.get_posts() == []


class TestGetComments:
    def test_request_params(self, api, requests_get):
        api.get_comments(42)

        assert requests_get.call_args.args == (f"{VK_URL}/wall.getComments",)
        params = call_params(requests_get)
        assert params["owner_id"] == str(GROUP_ID)
        assert params["post_id"] == 42
        assert params["count"] == 100
        assert params["sort"] == "asc"
        assert params["thread_items_count"] == 10

    def test_returns_items(self, api, requests_get):
        comments = [vk_comment(10), vk_comment(11)]
        requests_get.return_value = vk_response(
            {"response": {"count": 2, "items": comments}}
        )

        assert api.get_comments(42) == comments

    def test_vk_error(self, api, requests_get):
        requests_get.return_value = vk_response(vk_error(15, "Access denied"))

        assert api.get_comments(42) == []


class TestGetUsersNames:
    def test_returns_response_list(self, api, requests_get):
        users = [vk_user(1, "Иван", "Петров", 2)]
        requests_get.return_value = vk_response({"response": users})

        assert api.get_users_names({1}) == users
        assert requests_get.call_args.args == (f"{VK_URL}/users.get",)

    def test_vk_error(self, api, requests_get):
        requests_get.return_value = vk_response(vk_error())

        assert api.get_users_names({1}) == []


class TestGetGroupsNames:
    def test_returns_groups(self, api, requests_get):
        groups = [vk_group(5, "Театр"), vk_group(6, "Филармония")]
        requests_get.return_value = vk_response(
            {"response": {"groups": groups, "profiles": []}}
        )

        assert api.get_groups_names([5, 6]) == groups
        assert requests_get.call_args.args == (f"{VK_URL}/groups.getById",)
        assert call_params(requests_get)["group_ids"] == "5,6"

    def test_vk_error(self, api, requests_get):
        requests_get.return_value = vk_response(vk_error())

        assert api.get_groups_names([5]) == []
