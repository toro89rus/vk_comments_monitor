class Button:
    SUBSCRIBE = "Подписаться"
    UNSUBSCRIBE = "Отписаться"
    ACCEPT_SUB = "Принять"
    DECLINE_SUB = "Отклонить"
    REVIEW_PENDING_SUBS = "Обработать заявки"


class Message:
    WELCOME = "Привет! Подпишись для получения уведомлений"
    SUB_APPLICATION_SENT = (
        "Заявка отправлена. Я сообщу когда она будет обработана"
    )
    SUB_APPLICATION_ACCEPTED = (
        "Заявка одобрена. Я сообщу, когда появятся новые комментарии"
    )
    SUB_APPLICATION_DECLINED = "Заявка отклонена."
    ALREADY_SUBBED = "Подписка уже активна"
    ALREADY_PENDING = "Ваша заявка в обработке, подождите пожалуйста"
    NOT_SUBBED = "Вы не подписаны"
    APPLICATION_FROM = "Заявка от {name}"
    UNSUBBED = "Вы успешно отписались"
    USER_UNSUBBED = "{user_name} отписался"
    NO_PENDING_APPLICATIONS = "Новых заявок нет"
    PENDING_APPLICATIONS_LEN = "Всего заявок: {len}"
    APPLICATION = "Заявка от {user_name}"
