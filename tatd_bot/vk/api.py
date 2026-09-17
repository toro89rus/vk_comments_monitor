import logging

import requests

from tatd_bot.config import AppConfig

logger = logging.getLogger(__name__)


class VkApiService:

    def __init__(self, config: AppConfig):
        self.api_version = config.vk.api_version
        self.vk_url = config.vk.vk_url
        self.token = config.vk.token
        self.group_id = config.vk.group_id

    def _make_vk_call(self, method: str, *args, **params) -> dict:
        url = f"{self.vk_url}/{method}"
        params["access_token"] = self.token
        params["v"] = self.api_version
        for key, value in list(params.items()):
            if isinstance(value, (list, tuple, set)):
                params[key] = ",".join(map(str, value))
        try:
            r = requests.get(url, params=params, timeout=10)
            vk_response = r.json()
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

    def get_posts(self, count=20) -> list[dict]:
        api_response = self._make_vk_call(
            "wall.get", owner_id=self.group_id, count=count
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response["response"].get("items", [])

    def get_comments(
        self,
        post_id: int,
        thread_items_count: int = 10,
        count: int = 100,
    ) -> list[dict]:
        api_response = self._make_vk_call(
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

    def get_user_name(self, user_id: int) -> str:
        api_response = self._make_vk_call("users.get", user_ids=user_id)
        if not api_response or "response" not in api_response:
            return "Неизвестный пользователь"
        items = api_response["response"]
        if not items:
            return "Неизвестный пользователь"
        user = items[0]
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        user_name = f"{first_name} {last_name}".strip()
        return user_name or "Неизвестный пользователь"

    def get_group_name(self, group_id: int) -> str:
        api_response = self._make_vk_call("groups.getById", group_id=group_id)
        if not api_response or "response" not in api_response:
            return "Неизвестное сообщество"
        groups = api_response["response"].get("groups", [])
        if not groups:
            return "Неизвестное сообщество"
        return groups[0].get("name", "Неизвестное сообщество")

    def get_users_names(self, users_id: set | list) -> list[dict]:
        api_response = self._make_vk_call(
            "users.get", user_ids=users_id, fields=("sex",)
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response.get("response", [])

    def get_groups_names(self, group_ids: set | list) -> list[dict]:
        api_response = self._make_vk_call(
            "groups.getById", group_ids=group_ids
        )
        if not api_response or "response" not in api_response:
            return []
        return api_response["response"].get("groups", [])
