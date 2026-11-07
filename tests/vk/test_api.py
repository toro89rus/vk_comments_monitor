import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

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
    response.__aenter__.return_value = response
    response.json = AsyncMock(return_value=payload)
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
def session():
    session = MagicMock(closed=False)
    session.close = AsyncMock()
    session.get.return_value = vk_response({"response": {"items": []}})
    return session


@pytest.fixture
def http_get(session):
    return session.get


@pytest.fixture
def api(app_config, session):
    return VkApiService(app_config, session=session)


def call_params(http_get) -> dict:
    return http_get.call_args.kwargs["params"]


class TestRequest:
    async def test_url_token_version_and_timeout(self, api, http_get):
        await api.get_posts()

        http_get.assert_called_once()
        assert http_get.call_args.args == (f"{VK_URL}/wall.get",)
        assert http_get.call_args.kwargs["timeout"] == aiohttp.ClientTimeout(
            total=10
        )
        params = call_params(http_get)
        assert params["access_token"] == "vk-test-token"
        assert params["v"] == "5.199"

    @pytest.mark.parametrize(
        "call",
        [
            lambda api: api.get_posts(),
            lambda api: api.get_comments(1),
            lambda api: api.get_users_names([1]),
            lambda api: api.get_groups_names([1]),
        ],
        ids=["wall.get", "wall.getComments", "users.get", "groups.getById"],
    )
    async def test_every_request_asks_for_russian(self, api, http_get, call):
        await call(api)

        assert call_params(http_get)["lang"] == "ru"

    async def test_list_params_are_joined_with_commas(self, api, http_get):
        http_get.return_value = vk_response({"response": []})

        await api.get_users_names([1, 2, 3])

        params = call_params(http_get)
        assert params["user_ids"] == "1,2,3"
        assert params["fields"] == "sex"

    @pytest.mark.parametrize(
        "error",
        [aiohttp.ClientConnectionError("dns"), asyncio.TimeoutError()],
    )
    async def test_network_error_returns_empty_result(
        self, api, http_get, error, caplog
    ):
        http_get.side_effect = error

        assert await api.get_posts() == []
        assert "VK API network error while calling wall.get" in caplog.text

    async def test_invalid_json_returns_empty_result(self, api, http_get):
        http_get.return_value.json.side_effect = ValueError("not json")

        assert await api.get_posts() == []

    async def test_vk_error_returns_empty_result_and_is_logged(
        self, api, http_get, caplog
    ):
        http_get.return_value = vk_response(vk_error())

        assert await api.get_posts() == []
        assert "[5:None] User authorization failed" in caplog.text


class TestGetPosts:
    async def test_request_params(self, api, http_get):
        await api.get_posts()

        params = call_params(http_get)
        assert params["owner_id"] == str(GROUP_ID)
        assert params["count"] == 20

    async def test_returns_items(self, api, http_get):
        posts = [vk_post(1), vk_post(2)]
        http_get.return_value = vk_response(
            {"response": {"count": 2, "items": posts}}
        )

        assert await api.get_posts() == posts

    @pytest.mark.parametrize("payload", [{}, {"response": {}}])
    async def test_response_without_items(self, api, http_get, payload):
        http_get.return_value = vk_response(payload)

        assert await api.get_posts() == []


class TestGetComments:
    async def test_request_params(self, api, http_get):
        await api.get_comments(42)

        assert http_get.call_args.args == (f"{VK_URL}/wall.getComments",)
        params = call_params(http_get)
        assert params["owner_id"] == str(GROUP_ID)
        assert params["post_id"] == 42
        assert params["count"] == 100
        assert params["sort"] == "asc"
        assert params["thread_items_count"] == 10

    async def test_returns_items(self, api, http_get):
        comments = [vk_comment(10), vk_comment(11)]
        http_get.return_value = vk_response(
            {"response": {"count": 2, "items": comments}}
        )

        assert await api.get_comments(42) == comments

    async def test_vk_error(self, api, http_get):
        http_get.return_value = vk_response(vk_error(15, "Access denied"))

        assert await api.get_comments(42) == []


class TestGetUsersNames:
    async def test_returns_response_list(self, api, http_get):
        users = [vk_user(1, "Иван", "Петров", 2)]
        http_get.return_value = vk_response({"response": users})

        assert await api.get_users_names({1}) == users
        assert http_get.call_args.args == (f"{VK_URL}/users.get",)

    async def test_vk_error(self, api, http_get):
        http_get.return_value = vk_response(vk_error())

        assert await api.get_users_names({1}) == []


class TestGetGroupsNames:
    async def test_returns_groups(self, api, http_get):
        groups = [vk_group(5, "Театр"), vk_group(6, "Филармония")]
        http_get.return_value = vk_response(
            {"response": {"groups": groups, "profiles": []}}
        )

        assert await api.get_groups_names([5, 6]) == groups
        assert http_get.call_args.args == (f"{VK_URL}/groups.getById",)
        assert call_params(http_get)["group_ids"] == "5,6"

    async def test_vk_error(self, api, http_get):
        http_get.return_value = vk_response(vk_error())

        assert await api.get_groups_names([5]) == []


class TestSession:
    async def test_close_closes_session(self, api, session):
        await api.close()

        session.close.assert_awaited_once()

    async def test_close_without_session(self, app_config):
        await VkApiService(app_config).close()


@pytest.fixture
def clock():
    # подменяется ссылка на модуль time внутри api, а не time.monotonic:
    # на нём работают часы event loop
    with (
        patch("tatd_bot.vk.api.time") as fake_time,
        patch("tatd_bot.vk.api.asyncio.sleep", new=AsyncMock()) as sleep,
    ):
        yield fake_time.monotonic, sleep


class TestRateLimit:
    def test_default_interval_keeps_under_3_requests_per_second(self, api):
        assert api.request_interval > 1 / 3

    async def test_first_request_does_not_wait(self, api, clock):
        monotonic, sleep = clock
        monotonic.return_value = 100.0

        await api.get_posts()

        sleep.assert_not_awaited()

    async def test_next_request_waits_rest_of_interval(self, api, clock):
        monotonic, sleep = clock
        # конец первого запроса, проверка перед вторым, конец второго
        monotonic.side_effect = [100.0, 100.1, 100.35]

        await api.get_posts()
        await api.get_posts()

        sleep.assert_awaited_once()
        assert sleep.await_args.args[0] == pytest.approx(0.25)

    async def test_no_wait_after_interval_passed(self, api, clock):
        monotonic, sleep = clock
        monotonic.side_effect = [100.0, 101.0, 101.0]

        await api.get_posts()
        await api.get_posts()

        sleep.assert_not_awaited()

    async def test_failed_request_counts_for_interval(
        self, api, http_get, clock
    ):
        monotonic, sleep = clock
        monotonic.side_effect = [100.0, 100.1, 100.35]
        http_get.side_effect = [
            aiohttp.ClientConnectionError("dns"),
            vk_response({"response": {"items": []}}),
        ]

        await api.get_posts()
        await api.get_posts()

        sleep.assert_awaited_once()

    async def test_concurrent_calls_are_serialized(self, api, http_get):
        api.request_interval = 0
        in_flight = 0
        max_in_flight = 0

        async def slow_json(content_type=None):
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            await asyncio.sleep(0)
            in_flight -= 1
            return {"response": {"items": []}}

        http_get.return_value.json = slow_json

        await asyncio.gather(api.get_posts(), api.get_posts(), api.get_posts())

        assert http_get.call_count == 3
        assert max_in_flight == 1
