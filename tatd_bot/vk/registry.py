from dataclasses import dataclass, field

from tatd_bot.vk.models import Group, User


@dataclass
class AuthorsRegistry:
    users: dict[int, User] = field(default_factory=dict)
    groups: dict[int, Group] = field(default_factory=dict)

    def get_existing_user(self, uid: int) -> User | None:
        return self.users.get(uid)

    def register_user(self, user: User) -> None:
        self.users[user.id] = user

    def get_existing_group(self, gid: int) -> Group | None:
        return self.groups.get(gid)

    def register_group(self, group: Group) -> None:
        self.groups[group.id] = group


authors_registry = AuthorsRegistry()
