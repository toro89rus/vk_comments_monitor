"""Удаляет из кэша авторов имена, полученные латиницей.

До `lang=ru` в запросах VK с сервера отдавал имена транслитом. Кэш живёт
30 дней и не обновляется, поэтому такие имена удаляются: на ближайшем проходе
они запросятся у VK заново, уже по-русски.
"""

import logging
import re

from redis import asyncio as redis

logger = logging.getLogger(__name__)

# Ключи — как на момент миграции, не из репозитория: он может поменяться
USER_KEYS = "user:*"
USER_NAME_FIELDS = ("first_name", "last_name")
GROUP_KEYS = "group:*:name"
GROUP_NAME_FIELD = "name"

LATIN = re.compile("[A-Za-z]")


def _has_latin(*values: str | None) -> bool:
    return any(value and LATIN.search(value) for value in values)


async def _delete_latin(
    client: redis.Redis, pattern: str, fields: tuple[str, ...]
) -> int:
    deleted = 0
    async for key in client.scan_iter(match=pattern):
        if _has_latin(*await client.hmget(key, fields)):
            deleted += await client.delete(key)
    return deleted


async def migrate(client: redis.Redis) -> None:
    users = await _delete_latin(client, USER_KEYS, USER_NAME_FIELDS)
    groups = await _delete_latin(client, GROUP_KEYS, (GROUP_NAME_FIELD,))
    logger.info(
        "Deleted cached latin names: %s users, %s groups", users, groups
    )
