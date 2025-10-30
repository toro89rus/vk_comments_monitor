import telebot
from src.logger import logger
from config.settings import CHAT_ID, TG_API_TOKEN, VK_GROUP_ID


logger = logger.getChild(__name__)


def send_ya_maps_reviews(reviews_list):
    bot = telebot.TeleBot(TG_API_TOKEN)
    bot.send_message(CHAT_ID, f"Привет, новые комментарии: {len(reviews_list)}")
    for review in reviews_list:
        bot.send_message(
            CHAT_ID, f"Комментарий от {review["date"]}\n{review["text"]}"
        )


def send_vk_comments(vk_comments):
    bot = telebot.TeleBot(TG_API_TOKEN)
    for post in vk_comments:
        welcome_msg = (
            f"Новый комментарий к "
            f"<a href='https://vk.com/tuldramteatr?w=wall{VK_GROUP_ID}_"
            f"{post["post_id"]}'>посту</a> от {post["post_date"]}"
            f"\n{post["post_text"]}"
        )
        bot.send_message(CHAT_ID, welcome_msg, parse_mode="html")
        for comment in post["new_comments"]:
            comment_msg = format_msg(comment)
            bot.send_message(CHAT_ID, comment_msg)


def format_msg(comment):
    time = comment["comment_time"]
    text = comment["text"]
    author = comment["author"]
    message = f" Комментарий от {author} {time}\n{text}"
    return message
