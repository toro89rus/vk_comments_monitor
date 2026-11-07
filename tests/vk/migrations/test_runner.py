import pytest

from tatd_bot.vk.migrations.runner import (
    APPLIED_MIGRATIONS_KEY,
    MIGRATIONS,
    Migration,
    run_migrations,
)


def recording_migration(name: str, calls: list[str]) -> Migration:
    async def migrate(client) -> None:
        calls.append(name)

    return Migration(name, migrate)


async def test_applies_in_order_and_marks_applied(redis_client):
    calls: list[str] = []
    migrations = (
        recording_migration("001", calls),
        recording_migration("002", calls),
    )

    applied = await run_migrations(redis_client, migrations)

    assert applied == ["001", "002"]
    assert calls == ["001", "002"]
    assert await redis_client.smembers(APPLIED_MIGRATIONS_KEY) == {"001", "002"}


async def test_applied_migration_is_skipped(redis_client):
    calls: list[str] = []
    migrations = (
        recording_migration("001", calls),
        recording_migration("002", calls),
    )
    await redis_client.sadd(APPLIED_MIGRATIONS_KEY, "001")

    applied = await run_migrations(redis_client, migrations)

    assert applied == ["002"]
    assert calls == ["002"]


async def test_second_run_applies_nothing(redis_client):
    calls: list[str] = []
    migrations = (recording_migration("001", calls),)
    await run_migrations(redis_client, migrations)

    assert await run_migrations(redis_client, migrations) == []
    assert calls == ["001"]


async def test_failed_migration_is_not_marked_and_stops_run(redis_client):
    calls: list[str] = []

    async def broken(client) -> None:
        raise RuntimeError("broken")

    migrations = (Migration("001", broken), recording_migration("002", calls))

    with pytest.raises(RuntimeError):
        await run_migrations(redis_client, migrations)

    assert calls == []
    assert await redis_client.smembers(APPLIED_MIGRATIONS_KEY) == set()


def test_migration_names_are_unique():
    names = [migration.name for migration in MIGRATIONS]
    assert len(names) == len(set(names))


async def test_real_migrations_run_on_empty_redis(redis_client):
    applied = await run_migrations(redis_client)

    assert applied == [migration.name for migration in MIGRATIONS]
