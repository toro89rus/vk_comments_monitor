from tatd_bot.vk.migrations import (
    redis_migration_006_reset_latin_author_names as migration_006,
)

migrate = migration_006.migrate


async def save_user(redis_client, user_id: int, first: str, last: str) -> None:
    await redis_client.hset(
        f"user:{user_id}",
        mapping={"first_name": first, "last_name": last, "gender": "male"},
    )


async def save_group(redis_client, group_id: int, name: str) -> None:
    await redis_client.hset(f"group:{group_id}:name", "name", name)


async def test_deletes_latin_users_and_keeps_cyrillic(redis_client):
    await save_user(redis_client, 1, "Ivan", "Petrov")
    await save_user(redis_client, 2, "Иван", "Petrov")
    await save_user(redis_client, 3, "Иван", "Петров")

    await migrate(redis_client)

    assert await redis_client.exists("user:1", "user:2") == 0
    assert await redis_client.hgetall("user:3") == {
        "first_name": "Иван",
        "last_name": "Петров",
        "gender": "male",
    }


async def test_deletes_latin_groups_and_keeps_cyrillic(redis_client):
    await save_group(redis_client, 5, "Tulskiy teatr")
    await save_group(redis_client, 6, "Тульский театр")

    await migrate(redis_client)

    assert await redis_client.exists("group:5:name") == 0
    assert await redis_client.hget("group:6:name", "name") == "Тульский театр"


async def test_keeps_other_keys_and_ttl(redis_client):
    await save_user(redis_client, 3, "Иван", "Петров")
    await redis_client.expire("user:3", 100)
    await redis_client.hset("comment:7", "is_processed", 1)
    await redis_client.sadd("subscribers", 1)
    await redis_client.hset("bot_user:1", "full_name", "Ivan Petrov")

    await migrate(redis_client)

    assert await redis_client.ttl("user:3") == 100
    assert (
        await redis_client.exists("comment:7", "subscribers", "bot_user:1") == 3
    )


async def test_user_without_name_is_kept(redis_client):
    await save_user(redis_client, 4, "", "")

    await migrate(redis_client)

    assert await redis_client.exists("user:4") == 1


async def test_second_run_changes_nothing(redis_client):
    await save_user(redis_client, 1, "Ivan", "Petrov")
    await save_user(redis_client, 3, "Иван", "Петров")
    await migrate(redis_client)
    keys_after_first_run = sorted(await redis_client.keys("*"))

    await migrate(redis_client)

    assert sorted(await redis_client.keys("*")) == keys_after_first_run
    assert await redis_client.hget("user:3", "first_name") == "Иван"
