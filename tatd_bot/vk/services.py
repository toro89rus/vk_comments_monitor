import logging
from datetime import date, timedelta

from petrovich.enums import Gender

from tatd_bot.repository import Repository
from tatd_bot.utils.time_utils import get_msk_time
from tatd_bot.vk.api import VkApiService
from tatd_bot.vk.mappers import vk_to_post, vk_to_vk_user_base_data
from tatd_bot.vk.models import Comment, Group, Post, Reply, User
from tatd_bot.vk.registry import AuthorsRegistry
from tatd_bot.vk.text_formatting import format_comment_text, format_reply_text

logger = logging.getLogger(__name__)


class VkAuthorService:
    def __init__(self, registry: AuthorsRegistry, repo: Repository):
        self.registry = registry
        self.repo = repo

    def get_or_create_author(self, id: int) -> User | Group:
        if id < 0:
            gid = abs(id)
            return self._get_or_create_group(gid)

        return self._get_or_create_user(id)

    def _get_or_create_group(self, gid: int) -> Group:
        cached_local_group = self.registry.get_existing_group(gid)
        if cached_local_group:
            return cached_local_group

        cached_external_group_name = self.repo.get_group_name(gid)
        if cached_external_group_name:
            group = Group(gid, cached_external_group_name)
            self.registry.register_group(group)
            return group

        group = Group(gid)
        self.registry.register_group(group)
        return group

    def _get_or_create_user(self, uid: int) -> User:
        cached_local_user = self.registry.get_existing_user(uid)
        if cached_local_user:
            return cached_local_user

        cached_external_user = self.repo.get_user(uid)
        if cached_external_user:
            first_name = cached_external_user.get("first_name")
            last_name = cached_external_user.get("last_name")
            gender_raw = cached_external_user.get("gender")
            gender = (
                gender_raw
                if gender_raw in (Gender.MALE, Gender.FEMALE, Gender.ANDRGN)
                else None
            )
            user = User(uid, first_name, last_name, gender)
            self.registry.register_user(user)
            return user

        user = User(uid)
        self.registry.register_user(user)
        return user

    def update_users_from_vk(self, vk_users: list[dict]) -> None:
        for vk_user in vk_users:
            user = self.registry.get_existing_user(vk_user["id"])
            if user:
                base_data = vk_to_vk_user_base_data(vk_user)
                user.update(base_data)
                self.repo.save_user(
                    user.id,
                    user.first_name or "",
                    user.last_name or "",
                    user.gender or "",
                )

    def update_groups_from_vk(self, vk_groups: list[dict]) -> None:
        for vk_group in vk_groups:
            group = self.registry.get_existing_group(vk_group["id"])
            if group:
                group.update(vk_group)
                if group.name:
                    self.repo.save_group_name(group.id, group.name)


class VkMessageService:
    def __init__(self, author_service: VkAuthorService, repo: Repository):
        self.author_service = author_service
        self.repo = repo

    def make_comment(self, vk_comment: dict) -> Comment:
        return Comment(
            id=vk_comment["id"],
            created_at=get_msk_time(vk_comment["date"]),
            author=self._get_author(vk_comment),
            text=format_comment_text(vk_comment.get("text", "")),
            replies=[],
            is_new=not self.repo.is_comment_processed(vk_comment["id"]),
        )

    def make_reply(self, vk_comment: dict) -> Reply:
        return Reply(
            id=vk_comment["id"],
            created_at=get_msk_time(vk_comment["date"]),
            author=self._get_author(vk_comment),
            text=format_reply_text(vk_comment.get("text", "")),
            reply_to=self.author_service.get_or_create_author(
                vk_comment.get("reply_to_user", 0)
            ),
        )

    def _get_author(self, vk_comment: dict) -> User | Group:
        return self.author_service.get_or_create_author(vk_comment["from_id"])


class VkFeedService:
    def __init__(
        self,
        api: VkApiService,
        author_service: VkAuthorService,
        message_service: VkMessageService,
        repo: Repository,
    ):
        self.api = api
        self.author_service = author_service
        self.message_service = message_service
        self.repo = repo

    def get_new_comments(self) -> list[Post]:
        logger.info("Started new comments collecting")
        recent_posts = self._get_recent_posts_with_comments()
        posts_with_new_comments = []
        for post in recent_posts:
            if post_new_comments := self._get_new_comments_for_post(post):
                posts_with_new_comments.append(post_new_comments)
        if posts_with_new_comments:
            authors_ids = self._collect_author_ids(posts_with_new_comments)
            self._update_authors_names(authors_ids)
        return posts_with_new_comments

    def _get_recent_posts_with_comments(self, days: int = 7) -> list[dict]:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        posts = self.api.get_posts()
        recent_posts_with_comments = []
        for post in posts:
            post_date = date.fromtimestamp(post["date"])
            post_has_comments = post.get("comments", {}).get("count", 0) > 0
            if post_has_comments and post_date >= start_date:
                recent_posts_with_comments.append(post)
        return recent_posts_with_comments

    def _get_new_comments_for_post(self, vk_post: dict) -> Post | None:
        post_new_comments = []
        post_comments = self.api.get_comments(vk_post["id"])

        for comment in post_comments:
            formatted_comment = self._format_comment(comment)
            if formatted_comment:
                post_new_comments.append(formatted_comment)

        if post_new_comments:
            return vk_to_post(vk_post, post_new_comments)
        return None

    def _format_comment(self, vk_comment: dict) -> Comment | None:
        formatted_comment = self.message_service.make_comment(vk_comment)
        if vk_comment.get("thread", {}).get("count", 0) > 0:
            formatted_comment.replies = self._get_new_replies(vk_comment)
        if formatted_comment.has_new_activity():
            return formatted_comment
        return None

    def _get_new_replies(self, vk_comment: dict) -> list[Reply]:
        last_reply_id = self.repo.get_last_reply_id(vk_comment["id"]) or 0
        new_replies = []
        vk_replies = vk_comment.get("thread", {}).get("items", [])
        for reply in vk_replies:
            if reply["id"] > last_reply_id:
                serialized_reply = self.message_service.make_reply(reply)
                if serialized_reply.text:
                    new_replies.append(serialized_reply)
        return new_replies

    def _collect_author_ids(self, posts: list[Post]) -> dict[str, set[int]]:
        users_ids: set[int] = set()
        groups_ids: set[int] = set()
        author_type_mapping = {"user": users_ids, "group": groups_ids}

        for post in posts:
            for comment in post.comments:
                if not comment.author.name:
                    author_type_mapping[comment.author.kind].add(
                        comment.author.id
                    )
                for reply in comment.replies:
                    if not reply.author.name:
                        author_type_mapping[reply.author.kind].add(
                            reply.author.id
                        )
                    if not reply.reply_to.name:
                        author_type_mapping[reply.reply_to.kind].add(
                            reply.reply_to.id
                        )

        return {"users_ids": users_ids, "groups_ids": groups_ids}

    def _update_authors_names(self, authors_ids: dict[str, set[int]]) -> None:
        users_to_fetch = authors_ids["users_ids"]
        groups_to_fetch = authors_ids["groups_ids"]

        if users_to_fetch:
            vk_users = self.api.get_users_names(users_to_fetch)
            if vk_users:
                self.author_service.update_users_from_vk(vk_users)

        if groups_to_fetch:
            vk_groups = self.api.get_groups_names(groups_to_fetch)
            if vk_groups:
                self.author_service.update_groups_from_vk(vk_groups)

    def save_comments_cache(self, posts: list[Post]) -> None:
        for post in posts:
            for comment in post.comments:
                if comment.is_new:
                    self.repo.process_comment(comment.id)
                if comment.replies:
                    last_reply_id = comment.replies[-1].id
                    self.repo.save_last_reply_id(comment.id, last_reply_id)
