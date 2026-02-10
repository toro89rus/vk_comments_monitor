from aiogram.types import KeyboardButton

subscribe = KeyboardButton(text="Подписаться")
unsubscribe = KeyboardButton(text="Отписаться")
accept_subscriber = KeyboardButton(text="{chat_id} Одобрить заявку")
decline_subscriber = KeyboardButton(text="{chat_id} Отклонить заявку")
