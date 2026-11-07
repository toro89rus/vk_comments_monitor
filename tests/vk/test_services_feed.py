import pytest
from petrovich.enums import Gender

from tatd_bot.vk.models import Group, User
from tatd_bot.vk.registry import AuthorsRegistry
from tatd_bot.vk.services import (
    VkAuthorService,
    VkFeedService,
    VkMessageService,
)
from tests.vk.samples import (
    FakeVkApi,
    vk_comment,
    vk_group,
    vk_post,
    vk_reply,
    vk_user,
)


@pytest.fixture
def api():
    return FakeVkApi()


@pytest.fixture
def feed_service(api, vk_repo):
    author_service = VkAuthorService(AuthorsRegistry(), vk_repo)
    message_service = VkMessageService(author_service, vk_repo)
    return VkFeedService(api, author_service, message_service, vk_repo)


def comment_ids(posts) -> dict[int, list[int]]:
    return {post.id: [c.id for c in post.comments] for post in posts}


def reply_ids(posts) -> dict[int, list[int]]:
    return {
        comment.id: [reply.id for reply in comment.replies]
        for post in posts
        for comment in post.comments
    }


class TestRecentPosts:
    async def test_no_posts(self, feed_service):
        assert await feed_service.get_new_comments() == []

    async def test_only_recent_posts_with_comments_are_checked(
        self, feed_service, api
    ):
        api.posts = [
            vk_post(1, days_old=1),
            vk_post(2, days_old=6.5),
            vk_post(3, days_old=8),
            vk_post(4, days_old=1, comments_count=0),
        ]

        await feed_service.get_new_comments()

        assert api.comments_requests == [1, 2]

    async def test_post_without_comments_key_is_skipped(
        self, feed_service, api
    ):
        post = vk_post(1)
        del post["comments"]
        api.posts = [post]

        await feed_service.get_new_comments()

        assert api.comments_requests == []


class TestNewComments:
    async def test_new_comment_is_returned_with_post(self, feed_service, api):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10)]}

        posts = await feed_service.get_new_comments()

        assert comment_ids(posts) == {1: [10]}
        assert posts[0].text == "Текст поста 1"
        assert posts[0].comments[0].is_new is True

    async def test_processed_comment_is_skipped(
        self, feed_service, api, vk_repo
    ):
        await vk_repo.process_comment(10)
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10), vk_comment(11)]}

        assert comment_ids(await feed_service.get_new_comments()) == {1: [11]}

    async def test_post_without_new_comments_is_omitted(
        self, feed_service, api, vk_repo
    ):
        await vk_repo.process_comment(10)
        api.posts = [vk_post(1), vk_post(2)]
        api.comments = {1: [vk_comment(10)], 2: [vk_comment(20)]}

        assert comment_ids(await feed_service.get_new_comments()) == {2: [20]}

    async def test_new_comment_with_filtered_text_is_skipped(
        self, feed_service, api
    ):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10, text="Спасибо!")]}

        assert await feed_service.get_new_comments() == []

    async def test_comment_order_is_kept(self, feed_service, api):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(12), vk_comment(10), vk_comment(11)]}

        assert comment_ids(await feed_service.get_new_comments()) == {
            1: [12, 10, 11]
        }


class TestNewReplies:
    async def test_all_replies_of_new_comment_are_new(self, feed_service, api):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [vk_comment(10, replies=[vk_reply(11), vk_reply(12)])]
        }

        assert reply_ids(await feed_service.get_new_comments()) == {
            10: [11, 12]
        }

    async def test_only_replies_after_last_sent_are_new(
        self, feed_service, api, vk_repo
    ):
        await vk_repo.process_comment(10)
        await vk_repo.save_last_reply_id(10, 12)
        api.posts = [vk_post(1)]
        api.comments = {
            1: [
                vk_comment(
                    10,
                    replies=[vk_reply(11), vk_reply(12), vk_reply(13)],
                )
            ]
        }

        posts = await feed_service.get_new_comments()

        assert reply_ids(posts) == {10: [13]}
        assert posts[0].comments[0].is_new is False

    async def test_processed_comment_without_new_replies_is_skipped(
        self, feed_service, api, vk_repo
    ):
        await vk_repo.process_comment(10)
        await vk_repo.save_last_reply_id(10, 12)
        api.posts = [vk_post(1)]
        api.comments = {
            1: [vk_comment(10, replies=[vk_reply(11), vk_reply(12)])]
        }

        assert await feed_service.get_new_comments() == []

    async def test_replies_with_filtered_text_are_skipped(
        self, feed_service, api
    ):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [
                vk_comment(
                    10,
                    replies=[
                        vk_reply(11, text="[id1|Иван], спасибо"),
                        vk_reply(12, text="[id1|Иван], согласен"),
                    ],
                )
            ]
        }

        posts = await feed_service.get_new_comments()

        assert reply_ids(posts) == {10: [12]}
        assert posts[0].comments[0].replies[0].text == "согласен"

    async def test_comment_with_filtered_text_but_new_replies_is_returned(
        self, feed_service, api
    ):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [vk_comment(10, text="Спасибо!", replies=[vk_reply(11)])]
        }

        posts = await feed_service.get_new_comments()

        # текущее поведение: подписчику уйдёт комментарий с пустым текстом
        assert reply_ids(posts) == {10: [11]}
        assert posts[0].comments[0].text == ""

    async def test_replies_are_taken_only_from_thread_items(
        self, feed_service, api
    ):
        comment = vk_comment(10, replies=[vk_reply(11)])
        comment["thread"]["count"] = 15
        api.posts = [vk_post(1)]
        api.comments = {1: [comment]}

        # текущее поведение: count больше items, но остальные ответы
        # не запрашиваются
        assert reply_ids(await feed_service.get_new_comments()) == {10: [11]}

    async def test_thread_items_are_ignored_when_count_is_zero(
        self, feed_service, api
    ):
        comment = vk_comment(10, replies=[vk_reply(11)])
        comment["thread"]["count"] = 0
        api.posts = [vk_post(1)]
        api.comments = {1: [comment]}

        assert reply_ids(await feed_service.get_new_comments()) == {10: []}


class TestAuthorsNames:
    async def test_unknown_authors_are_fetched_in_one_batch(
        self, feed_service, api
    ):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [
                vk_comment(
                    10,
                    from_id=1,
                    replies=[vk_reply(11, from_id=2, reply_to_user=1)],
                ),
                vk_comment(12, from_id=-5),
            ]
        }
        api.users = [
            vk_user(1, "Иван", "Петров", 2),
            vk_user(2, "Мария", "Иванова", 1),
        ]
        api.groups = [vk_group(5, "Театр")]

        posts = await feed_service.get_new_comments()

        assert api.users_requests == [{1, 2}]
        assert api.groups_requests == [{5}]
        first, second = posts[0].comments
        assert first.author == User(1, "Иван", "Петров", Gender.MALE)
        assert first.replies[0].author.name_gen == "Марии Ивановой"
        assert first.replies[0].reply_to is first.author
        assert second.author == Group(5, "Театр")

    async def test_authors_known_from_redis_are_not_fetched(
        self, feed_service, api, vk_repo
    ):
        await vk_repo.save_user(1, "Иван", "Петров", Gender.MALE)
        await vk_repo.save_group_name(5, "Театр")
        api.posts = [vk_post(1)]
        api.comments = {
            1: [vk_comment(10, from_id=1), vk_comment(11, from_id=-5)]
        }

        await feed_service.get_new_comments()

        assert api.users_requests == []
        assert api.groups_requests == []

    async def test_fetched_names_are_saved_to_redis(
        self, feed_service, api, vk_repo
    ):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10, from_id=1)]}
        api.users = [vk_user(1, "Иван", "Петров", 2)]

        await feed_service.get_new_comments()

        assert (await vk_repo.get_user(1))["first_name"] == "Иван"

    async def test_author_missing_in_vk_response_stays_unknown(
        self, feed_service, api
    ):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10, from_id=1)]}

        posts = await feed_service.get_new_comments()

        assert str(posts[0].comments[0].author) == "Неизвестный пользователь"

    async def test_reply_without_reply_to_user_requests_user_zero(
        self, feed_service, api
    ):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [vk_comment(10, replies=[vk_reply(11, reply_to_user=None)])]
        }

        await feed_service.get_new_comments()

        # текущее поведение: в users.get уходит id 0
        assert api.users_requests == [{0, 1, 2}]

    async def test_no_names_requested_when_nothing_new(
        self, feed_service, api, vk_repo
    ):
        await vk_repo.process_comment(10)
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10)]}

        await feed_service.get_new_comments()

        assert api.users_requests == []


class TestSaveCommentsCache:
    async def test_new_comment_is_marked_processed(
        self, feed_service, api, vk_repo
    ):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10)]}

        await feed_service.save_comments_cache(
            await feed_service.get_new_comments()
        )

        assert await vk_repo.is_comment_processed(10) is True
        assert await vk_repo.get_last_reply_id(10) is None
        assert await feed_service.get_new_comments() == []

    async def test_last_reply_id_is_saved(self, feed_service, api, vk_repo):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [vk_comment(10, replies=[vk_reply(11), vk_reply(12)])]
        }

        await feed_service.save_comments_cache(
            await feed_service.get_new_comments()
        )

        assert await vk_repo.get_last_reply_id(10) == 12
        assert await feed_service.get_new_comments() == []

    async def test_last_reply_id_is_the_last_returned_reply(
        self, feed_service, api, vk_repo
    ):
        api.posts = [vk_post(1)]
        api.comments = {
            1: [
                vk_comment(
                    10,
                    replies=[
                        vk_reply(11),
                        vk_reply(12, text="[id1|Иван], спасибо"),
                    ],
                )
            ]
        }

        await feed_service.save_comments_cache(
            await feed_service.get_new_comments()
        )

        # отфильтрованный ответ 12 не сохраняется, но и не уйдёт повторно
        assert await vk_repo.get_last_reply_id(10) == 11
        assert await feed_service.get_new_comments() == []

    async def test_filtered_new_comment_is_never_marked_processed(
        self, feed_service, api, vk_repo
    ):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10, text="Спасибо!")]}

        await feed_service.save_comments_cache(
            await feed_service.get_new_comments()
        )

        # текущее поведение: проверяется заново на каждом проходе
        assert await vk_repo.is_comment_processed(10) is False

    async def test_new_reply_to_processed_comment(
        self, feed_service, api, vk_repo
    ):
        api.posts = [vk_post(1)]
        api.comments = {1: [vk_comment(10, replies=[vk_reply(11)])]}
        await feed_service.save_comments_cache(
            await feed_service.get_new_comments()
        )

        api.comments = {
            1: [vk_comment(10, replies=[vk_reply(11), vk_reply(12)])]
        }
        posts = await feed_service.get_new_comments()

        assert reply_ids(posts) == {10: [12]}
        assert posts[0].comments[0].is_new is False


class TestVkRequestsAreSequential:
    async def test_requests_never_overlap(self, feed_service, api):
        # У VK лимит частоты запросов: async нужен, чтобы не блокировать бота,
        # а запросы к VK должны идти строго по одному
        api.posts = [vk_post(1), vk_post(2), vk_post(3)]
        api.comments = {
            1: [vk_comment(10, from_id=1)],
            2: [vk_comment(20, from_id=-5)],
            3: [vk_comment(30, from_id=2)],
        }

        await feed_service.get_new_comments()

        assert api.comments_requests == [1, 2, 3]
        assert api.users_requests and api.groups_requests
        assert api.max_in_flight == 1
