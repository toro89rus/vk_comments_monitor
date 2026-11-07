import logging

import aiohttp

from tatd_bot.config import AppConfig

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class VkApiService:
    def __init__(
        self, config: AppConfig, session: aiohttp.ClientSession | None = None
    ):
        self.api_version = config.vk.api_version
        self.vk_url = config.vk.vk_url
        self.token = config.vk.token
        self.group_id = config.vk.group_id
        self._session = session

    def _get_session(self) -> aiohttp.ClientSession:
        # сессию создаём внутри работающего event loop, при первом запросе
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()

    async def _make_vk_call(self, method: str, *args, **params) -> dict:
        url = f"{self.vk_url}/{method}"
        params["access_token"] = self.token
        params["v"] = self.api_version
        for key, value in list(params.items()):
            if isinstance(value, (list, tuple, set)):
                params[key] = ",".join(map(str, value))
        try:
            async with self._get_session().get(
                url, params=params, timeout=REQUEST_TIMEOUT
            ) as r:
                vk_response = await r.json(content_type=None)
        except Exception:
            logger.exception("VK API network error while calling %s", method)
            return {}

        if "error" in vk_response:
            error = vk_response["error"]
            error_code = error.get("error_code")
            error_subcode = error.get("error_subcode")
            error_msg = error.get("error_msg")
            logger.error(
                "VK API returned error for %s: [%s:%s] %s",
                method,
                error_code,
                error_subcode,
                error_msg,
            )
            return {}

        return vk_response

    async def get_posts(self, count=20) -> list[dict]:
        api_response = await self._make_vk_call(
            "wall.get", owner_id=self.group_id, count=count
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response["response"].get("items", [])

    async def get_comments(
        self,
        post_id: int,
        thread_items_count: int = 10,
        count: int = 100,
    ) -> list[dict]:
        api_response = await self._make_vk_call(
            "wall.getComments",
            owner_id=self.group_id,
            post_id=post_id,
            count=count,
            sort="asc",
            thread_items_count=thread_items_count,
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response["response"].get("items", [])

    async def get_users_names(self, users_id: set | list) -> list[dict]:
        api_response = await self._make_vk_call(
            "users.get", user_ids=users_id, fields=("sex",)
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response.get("response", [])

    async def get_groups_names(self, group_ids: set | list) -> list[dict]:
        api_response = await self._make_vk_call(
            "groups.getById", group_ids=group_ids
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response["response"].get("groups", [])
