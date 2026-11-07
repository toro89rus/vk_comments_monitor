"""Применяет миграции Redis при старте бота, каждую один раз."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from redis import asyncio as redis

logger = logging.getLogger(__name__)

APPLIED_MIGRATIONS_KEY = "migrations:applied"


@dataclass(frozen=True)
class Migration:
    name: str
    migrate: Callable[[redis.Redis], Awaitable[None]]


# По порядку применения. Новая миграция — в конец, имена не менять
MIGRATIONS: tuple[Migration, ...] = ()


async def run_migrations(
    client: redis.Redis, migrations: tuple[Migration, ...] = MIGRATIONS
) -> list[str]:
    """Применяет ещё не применённые миграции и возвращает их имена.
    Ошибка миграции не перехватывается: бот не стартует на данных,
    которые не удалось перевести в новый формат."""
    applied = []
    for migration in migrations:
        if await client.sismember(APPLIED_MIGRATIONS_KEY, migration.name):
            continue
        logger.info("Applying migration %s", migration.name)
        await migration.migrate(client)
        await client.sadd(APPLIED_MIGRATIONS_KEY, migration.name)
        applied.append(migration.name)
    return applied
