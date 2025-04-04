import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# DIRS
PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_STORAGE = PROJECT_ROOT / "storage"
LATEST_REVIEW_FILE_PATH = PROJECT_STORAGE / "latest_review.txt"
LATEST_VK_COMMENTS_FILE_PATH = PROJECT_STORAGE / "latest_vk_comments.json"
SCREENSHOTS_PATH = PROJECT_ROOT / "screenshots"
LOG_FILE_PATH = PROJECT_ROOT / "logs" / "app.log"

# CLOUD DIRS
CLOUD_SCREENSHOTS_PATH = "app:/screenshots"
CLOUD_LATEST_REVIEW_FILE_PATH = "app:/storage/latest_review.txt"
CLOUD_LATEST_VK_COMMENTS_FILE_PATH = "app:/storage/latest_vk_comments.json"

# TOKENS
TG_API_TOKEN = os.getenv("TG_API_TOKEN")
YANDEX_TOKEN = os.getenv("YANDEX_TOKEN")
VK_TOKEN = os.getenv("VK_TOKEN")

# YA_MAPS
YA_MAPS_URL = os.getenv("YA_MAPS_URL")

# TG
CHAT_ID = os.getenv("CHAT_ID")

# VK
VK_GROUP_ID = "-48164678"
