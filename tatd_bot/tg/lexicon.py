
class Button:
    SUBSCRIBE = "Подписаться"
    UNSUBSCRIBE = "Отписаться"
    ACCEPT_SUB = "Принять заявку от {chat_id}"
    DECLINE_SUB = "Отклонить заявку от {chat_id}"
    SUBS_LIST = "Посмотреть подписчиков"


class Message:
    WELCOME = "Привет! Подпишись для получения уведомлений"
    SUB_APPLICATION_SENT = (
        "Заявка отправлена. Я сообщу когда она будет обработана"
    )
    SUB_APPLICATION_ACCEPTED = (
        "Заявка одобрена. Я сообщу, когда появятся новые комментарии"
    )
    ALREADY_SUBBED = "Подписка уже активна"
    APPLICATION_FROM = "Заявка от {name}"
    UNSUBBED = "Вы успешно отписались"
    USER_UNSUBBED = "{user_name} отписался"
