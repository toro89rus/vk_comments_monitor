import telebot

from config.settings import CHAT_ID, TG_API_TOKEN
from src.vk.classes import Post
from src.logger import logger

logger = logger.getChild(__name__)


def send_ya_maps_reviews(reviews_list):
    bot = telebot.TeleBot(TG_API_TOKEN)
    bot.send_message(
        CHAT_ID, f"Привет, новые комментарии: {len(reviews_list)}"
    )
    for review in reviews_list:
        bot.send_message(
            CHAT_ID, f"Комментарий от {review["date"]}\n{review["text"]}"
        )


def send_vk_comments(vk_comments: list[Post]) -> None:
    bot = telebot.TeleBot(TG_API_TOKEN)
    for post in vk_comments:
        bot.send_message(CHAT_ID, str(post), parse_mode="html")
        for comment in post.comments:
            bot.send_message(CHAT_ID, str(comment))
