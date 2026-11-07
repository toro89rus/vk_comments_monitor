"""Синтетические ответы VK API 5.199 и фейковый VkApiService.

Собраны по документации (wall.get, wall.getComments, users.get,
groups.getById), а не сняты с настоящего API: токен VK привязан к IP сервера.
Поля — те, что читает код, плюс несколько соседних для правдоподобия.
"""

import asyncio
import time

GROUP_ID = -48164678
DAY = 24 * 60 * 60


def days_ago(days: float) -> int:
    return int(time.time() - days * DAY)


def vk_post(
    post_id: int, *, days_old: float = 1, comments_count: int = 1
) -> dict:
    return {
        "id": post_id,
        "owner_id": GROUP_ID,
        "from_id": GROUP_ID,
        "date": days_ago(days_old),
        "text": f"Текст поста {post_id}",
        "comments": {"count": comments_count, "can_post": 1},
        "likes": {"count": 0},
    }


def vk_reply(
    reply_id: int,
    *,
    from_id: int = 2,
    text: str = "Ответ",
    reply_to_user: int | None = 1,
    reply_to_comment: int | None = None,
) -> dict:
    reply = {
        "id": reply_id,
        "from_id": from_id,
        "date": days_ago(0.5),
        "text": text,
        "post_id": 1,
        "owner_id": GROUP_ID,
        "parents_stack": [],
    }
    if reply_to_user is not None:
        reply["reply_to_user"] = reply_to_user
    if reply_to_comment is not None:
        reply["reply_to_comment"] = reply_to_comment
    return reply


def vk_comment(
    comment_id: int,
    *,
    from_id: int = 1,
    text: str = "Отличный спектакль",
    replies: list[dict] | None = None,
) -> dict:
    replies = replies or []
    return {
        "id": comment_id,
        "from_id": from_id,
        "date": days_ago(0.5),
        "text": text,
        "post_id": 1,
        "owner_id": GROUP_ID,
        "parents_stack": [],
        "thread": {
            "count": len(replies),
            "items": replies,
            "can_post": True,
        },
    }


def vk_user(user_id: int, first_name: str, last_name: str, sex: int) -> dict:
    return {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "sex": sex,
        "can_access_closed": True,
        "is_closed": False,
    }


def vk_group(group_id: int, name: str) -> dict:
    return {
        "id": group_id,
        "name": name,
        "screen_name": f"club{group_id}",
        "is_closed": 0,
        "type": "group",
    }


class FakeVkApi:
    """Подмена VkApiService: отдаёт заданные данные и запоминает вызовы."""

    def __init__(
        self,
        posts: list[dict] | None = None,
        comments: dict[int, list[dict]] | None = None,
        users: list[dict] | None = None,
        groups: list[dict] | None = None,
    ):
        self.posts = posts or []
        self.comments = comments or {}
        self.users = users or []
        self.groups = groups or []
        self.comments_requests: list[int] = []
        self.users_requests: list[set[int]] = []
        self.groups_requests: list[set[int]] = []
        self.in_flight = 0
        self.max_in_flight = 0

    async def _request(self) -> None:
        # имитирует ожидание ответа: даёт event loop переключиться на другие
        # задачи, чтобы параллельные запросы были видны в max_in_flight
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0)
        self.in_flight -= 1

    async def get_posts(self, count: int = 20) -> list[dict]:
        await self._request()
        return self.posts

    async def get_comments(self, post_id: int, **kwargs) -> list[dict]:
        await self._request()
        self.comments_requests.append(post_id)
        return self.comments.get(post_id, [])

    async def get_users_names(self, users_id: set | list) -> list[dict]:
        await self._request()
        self.users_requests.append(set(users_id))
        return [user for user in self.users if user["id"] in users_id]

    async def get_groups_names(self, group_ids: set | list) -> list[dict]:
        await self._request()
        self.groups_requests.append(set(group_ids))
        return [group for group in self.groups if group["id"] in group_ids]
