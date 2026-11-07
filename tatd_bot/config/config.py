import os
from dataclasses import dataclass

from dotenv import load_dotenv

DATE_FORMAT = "%d.%m.%Y"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
LOG_FORMAT = "[{asctime}] #{levelname:8} - {name} - {message}"


@dataclass(frozen=True)
class VkConfig:
    token: str
    group_id: str = "-48164678"
    group_name: str = "tuldramteatr"
    vk_url: str = "https://api.vk.ru/method"
    api_version: str = "5.199"
    update_delay: int = 300

    @property
    def group_link(self):
        return f"https://vk.com/{self.group_name}?w=wall{self.group_id}"


@dataclass(frozen=True)
class TgConfig:
    token: str
    admin_id: int


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: int = 6379


@dataclass(frozen=True)
class AppConfig:
    vk: VkConfig
    tg: TgConfig
    redis: RedisConfig
    env: str
    date_format: str
    datetime_format: str
    log_format: str


def load_config() -> AppConfig:
    load_dotenv()
    vk_update_delay = int(os.getenv("VK_MONITOR_UPDATE_DELAY", "300"))
    vk = VkConfig(
        token=os.getenv("VK_TOKEN", ""),
        group_id=os.getenv("VK_GROUP_ID", "-48164678"),
        group_name=os.getenv("VK_GROUP_NAME", "tuldramteatr"),
        update_delay=vk_update_delay,
    )
    tg = TgConfig(
        token=os.getenv("TG_TOKEN", ""),
        admin_id=int(os.getenv("ADMIN_ID", "0")),
    )
    redis = RedisConfig(
        host=os.getenv("REDIS", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )
    return AppConfig(
        vk=vk,
        tg=tg,
        redis=redis,
        env=os.getenv("ENV", "PROD"),
        date_format=DATE_FORMAT,
        datetime_format=DATETIME_FORMAT,
        log_format=LOG_FORMAT,
    )
