import pytest
from petrovich.enums import Gender

from tatd_bot.vk.models import Comment, Group, Reply, User
from tatd_bot.vk.registry import AuthorsRegistry
from tatd_bot.vk.services import VkAuthorService, VkMessageService
from tests.vk.samples import vk_comment, vk_group, vk_reply, vk_user


@pytest.fixture
def registry():
    return AuthorsRegistry()


@pytest.fixture
def author_service(registry, vk_repo):
    return VkAuthorService(registry, vk_repo)


@pytest.fixture
def message_service(author_service, vk_repo):
    return VkMessageService(author_service, vk_repo)


class TestGetOrCreateAuthor:
    async def test_positive_id_is_user(self, author_service, registry):
        author = await author_service.get_or_create_author(1)

        assert author == User(1)
        assert registry.get_existing_user(1) is author

    async def test_negative_id_is_group_with_positive_id(
        self, author_service, registry
    ):
        author = await author_service.get_or_create_author(-5)

        assert author == Group(5)
        assert registry.get_existing_group(5) is author

    async def test_zero_id_is_user(self, author_service):
        # текущее поведение: ответ без reply_to_user адресован User(0)
        assert await author_service.get_or_create_author(0) == User(0)

    async def test_registered_author_is_reused(self, author_service):
        first = await author_service.get_or_create_author(1)

        assert await author_service.get_or_create_author(1) is first

    async def test_user_is_loaded_from_redis(self, author_service, vk_repo):
        await vk_repo.save_user(1, "Иван", "Петров", Gender.MALE)

        user = await author_service.get_or_create_author(1)

        assert user == User(1, "Иван", "Петров", Gender.MALE)
        assert user.name_gen == "Ивана Петрова"

    @pytest.mark.parametrize("stored_gender", ["", "unknown"])
    async def test_unknown_gender_from_redis_becomes_none(
        self, author_service, vk_repo, stored_gender
    ):
        await vk_repo.save_user(1, "Иван", "Петров", stored_gender)

        assert (await author_service.get_or_create_author(1)).gender is None

    async def test_group_is_loaded_from_redis(self, author_service, vk_repo):
        await vk_repo.save_group_name(5, "Театр")

        assert await author_service.get_or_create_author(-5) == Group(
            5, "Театр"
        )

    async def test_registry_wins_over_redis(self, author_service, vk_repo):
        # текущее поведение: имя из registry не обновляется до перезапуска
        await author_service.get_or_create_author(1)
        await vk_repo.save_user(1, "Иван", "Петров", Gender.MALE)

        assert (await author_service.get_or_create_author(1)).name is None


class TestUpdateAuthorsFromVk:
    async def test_updates_registered_user_and_saves_to_redis(
        self, author_service, vk_repo
    ):
        user = await author_service.get_or_create_author(1)

        await author_service.update_users_from_vk(
            [vk_user(1, "Иван", "Петров", 2)]
        )

        assert user == User(1, "Иван", "Петров", Gender.MALE)
        assert await vk_repo.get_user(1) == {
            "first_name": "Иван",
            "last_name": "Петров",
            "gender": "male",
        }

    async def test_user_without_gender_is_saved_with_empty_gender(
        self, author_service, vk_repo
    ):
        await author_service.get_or_create_author(1)

        await author_service.update_users_from_vk(
            [vk_user(1, "Иван", "Петров", 0)]
        )

        assert (await vk_repo.get_user(1))["gender"] == ""

    async def test_unregistered_user_is_ignored(self, author_service, vk_repo):
        await author_service.update_users_from_vk(
            [vk_user(1, "Иван", "Петров", 2)]
        )

        assert await vk_repo.get_user(1) == {}

    async def test_updates_registered_group_and_saves_to_redis(
        self, author_service, vk_repo
    ):
        group = await author_service.get_or_create_author(-5)

        await author_service.update_groups_from_vk([vk_group(5, "Театр")])

        assert group.name == "Театр"
        assert await vk_repo.get_group_name(5) == "Театр"

    async def test_group_without_name_is_not_saved(
        self, author_service, vk_repo
    ):
        await author_service.get_or_create_author(-5)

        await author_service.update_groups_from_vk([vk_group(5, "")])

        assert await vk_repo.get_group_name(5) is None

    async def test_unregistered_group_is_ignored(self, author_service, vk_repo):
        await author_service.update_groups_from_vk([vk_group(5, "Театр")])

        assert await vk_repo.get_group_name(5) is None


class TestMakeComment:
    async def test_new_comment(self, message_service):
        comment = await message_service.make_comment(vk_comment(10, from_id=1))

        assert isinstance(comment, Comment)
        assert comment.id == 10
        assert comment.author == User(1)
        assert comment.text == "Отличный спектакль"
        assert comment.replies == []
        assert comment.is_new is True

    async def test_processed_comment_is_not_new(self, message_service, vk_repo):
        await vk_repo.process_comment(10)

        assert (
            await message_service.make_comment(vk_comment(10))
        ).is_new is False

    async def test_comment_text_is_filtered(self, message_service):
        comment = await message_service.make_comment(
            vk_comment(10, text="Спасибо!")
        )

        assert comment.text == ""

    async def test_comment_from_group(self, message_service):
        comment = await message_service.make_comment(vk_comment(10, from_id=-5))

        assert comment.author == Group(5)

    async def test_replies_from_vk_are_not_attached(self, message_service):
        vk_data = vk_comment(10, replies=[vk_reply(11)])

        assert (await message_service.make_comment(vk_data)).replies == []


class TestMakeReply:
    async def test_reply(self, message_service):
        reply = await message_service.make_reply(
            vk_reply(11, from_id=2, reply_to_user=1, text="[id1|Иван], да")
        )

        assert isinstance(reply, Reply)
        assert reply.id == 11
        assert reply.author == User(2)
        assert reply.reply_to == User(1)
        assert reply.text == "да"

    async def test_reply_to_group(self, message_service):
        reply = await message_service.make_reply(vk_reply(11, reply_to_user=-5))

        assert reply.reply_to == Group(5)

    async def test_reply_without_reply_to_user(self, message_service, caplog):
        reply = await message_service.make_reply(
            vk_reply(11, reply_to_user=None)
        )

        # текущее поведение: адресат — User(0)
        assert reply.reply_to == User(0)
        assert "VK reply 11 on post 1 has no reply_to_user" in caplog.text

    async def test_reply_with_reply_to_user_is_not_logged(
        self, message_service, caplog
    ):
        await message_service.make_reply(vk_reply(11, reply_to_user=1))

        assert "reply_to_user" not in caplog.text

    async def test_authors_are_shared_between_messages(self, message_service):
        comment = await message_service.make_comment(vk_comment(10, from_id=1))
        reply = await message_service.make_reply(vk_reply(11, reply_to_user=1))

        assert reply.reply_to is comment.author
