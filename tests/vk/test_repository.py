from petrovich.enums import Gender

from tatd_bot.vk.repository import COMMENT_TTL, USER_TTL

DAY = 24 * 60 * 60


def test_ttl_values():
    assert USER_TTL == 30 * DAY
    assert COMMENT_TTL == 8 * DAY


class TestVkUser:
    async def test_save_and_get_user(self, vk_repo, redis_client):
        await vk_repo.save_user(1, "Иван", "Петров", Gender.MALE)

        assert await vk_repo.get_user(1) == {
            "first_name": "Иван",
            "last_name": "Петров",
            "gender": "male",
        }
        assert await redis_client.ttl("user:1") == USER_TTL

    async def test_get_missing_user_returns_empty_dict(self, vk_repo):
        assert await vk_repo.get_user(1) == {}

    async def test_save_user_overwrites_fields(self, vk_repo):
        await vk_repo.save_user(1, "Иван", "Петров", "male")
        await vk_repo.save_user(1, "Пётр", "", "")

        assert await vk_repo.get_user(1) == {
            "first_name": "Пётр",
            "last_name": "",
            "gender": "",
        }


class TestVkGroup:
    async def test_save_and_get_group_name(self, vk_repo, redis_client):
        await vk_repo.save_group_name(5, "Театр")

        assert await vk_repo.get_group_name(5) == "Театр"
        assert await redis_client.hgetall("group:5:name") == {"name": "Театр"}
        assert await redis_client.ttl("group:5:name") == USER_TTL

    async def test_get_missing_group_name(self, vk_repo):
        assert await vk_repo.get_group_name(5) is None


class TestComment:
    async def test_new_comment_is_not_processed(self, vk_repo):
        assert await vk_repo.is_comment_processed(1) is False

    async def test_process_comment(self, vk_repo, redis_client):
        await vk_repo.process_comment(1)

        assert await vk_repo.is_comment_processed(1) is True
        assert await redis_client.hgetall("comment:1") == {"is_processed": "1"}
        assert await redis_client.ttl("comment:1") == COMMENT_TTL

    async def test_last_reply_id(self, vk_repo, redis_client):
        assert await vk_repo.get_last_reply_id(1) is None

        await vk_repo.save_last_reply_id(1, 77)

        assert await vk_repo.get_last_reply_id(1) == 77
        assert await redis_client.ttl("comment:1") == COMMENT_TTL

    async def test_last_reply_id_does_not_mark_comment_processed(self, vk_repo):
        await vk_repo.save_last_reply_id(1, 77)

        assert await vk_repo.is_comment_processed(1) is False

    async def test_process_and_last_reply_share_one_hash(
        self, vk_repo, redis_client
    ):
        await vk_repo.process_comment(1)
        await vk_repo.save_last_reply_id(1, 77)

        assert await redis_client.hgetall("comment:1") == {
            "is_processed": "1",
            "last_reply_id": "77",
        }

    async def test_saving_reply_refreshes_ttl(self, vk_repo, redis_client):
        await vk_repo.process_comment(1)
        await redis_client.expire("comment:1", 10)

        await vk_repo.save_last_reply_id(1, 77)

        assert await redis_client.ttl("comment:1") == COMMENT_TTL
