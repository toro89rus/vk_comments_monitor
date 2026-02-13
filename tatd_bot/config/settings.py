import os

from dotenv import load_dotenv

load_dotenv()

# TOKENS
TG_API_TOKEN = os.getenv("TG_API_TOKEN")
VK_TOKEN = os.getenv("VK_TOKEN")

# TG
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# REDIS
REDIS_HOST = os.getenv("REDIS", "localhost")

# VK
VK_GROUP_ID = "-48164678"
VK_GROUP_NAME = "tuldramteatr"
VK_GROUP_LINK = f"https://vk.com/{VK_GROUP_NAME}?w=wall{VK_GROUP_ID}"

VK_MONITOR_UPDATE_DELAY = int(os.getenv("VK_MONITOR_UPDATE_DELAY"))

DATE_FORMAT = "%d.%m.%Y"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
ENV = os.getenv("ENV")
