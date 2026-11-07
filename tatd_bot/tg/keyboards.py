from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from tatd_bot.tg.lexicon import Button

USER_SUBSCRIBE = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=Button.SUBSCRIBE),
            KeyboardButton(text=Button.UNSUBSCRIBE),
        ]
    ],
    resize_keyboard=True,
)


ADMIN_REVIEW_PENDING = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=Button.ACCEPT_SUB),
            KeyboardButton(text=Button.DECLINE_SUB),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

ADMIN_PANEL = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=Button.SUBSCRIBE),
            KeyboardButton(text=Button.UNSUBSCRIBE),
        ],
        [KeyboardButton(text=Button.REVIEW_PENDING_SUBS)],
    ],
    resize_keyboard=True,
)
