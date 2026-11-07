# Баги и открытые вопросы

Здесь только то, что меняет поведение бота. Структурные правки без смены поведения — в
[refactoring.md](refactoring.md).

- **Баг** исправляется отдельным коммитом. В нём же меняется тест с пометкой «текущее поведение» и удаляется
  запись отсюда. История остаётся в git.
- **Вопрос** — нужны данные или решение владельца. После ответа вопрос становится багом, задачей
  рефакторинга или закрывается.
- Номера не переиспользуются: новая запись получает следующий свободный номер.

Приоритет: **высокий** — подписчики получают лишнее или теряют сообщения; **средний** — видимый дефект
в сообщениях; **низкий** — редкий случай или неудобство.

## Баги

### B2. «Комментарий от None» · средний

Если имя автора не пришло из VK, `name_gen` / `name_dat` у `User` и `Group` возвращают `None`, и в сообщение
попадает строка `None`. `str()` при этом даёт «Неизвестный пользователь» / «Неизвестная группа».

- Где: `tatd_bot/vk/models.py`, используется в `tatd_bot/tg/formatters.py`.
- Тесты: `tests/vk/test_models.py::TestUser::test_unknown_user`, `TestGroup::test_unknown_group`,
  `tests/tg/test_formatters.py::test_format_comment_author_name`.

### B4. Отфильтрованный комментарий с новыми ответами уходит пустым · низкий

Если текст комментария отфильтрован (например «Спасибо!»), но под ним есть новые ответы, подписчику
приходит «Комментарий от …» с пустым текстом. Нужно решить, что показывать: пометку вместо текста, только
ответы или исходный текст. Заодно: такой комментарий без ответов никогда не помечается `is_processed` и
проверяется заново на каждом проходе.

- Где: `VkFeedService._format_comment`, `save_comments_cache` (`tatd_bot/vk/services.py`).
- Тесты: `tests/vk/test_services_feed.py::TestNewReplies::test_comment_with_filtered_text_but_new_replies_is_returned`,
  `TestSaveCommentsCache::test_filtered_new_comment_is_never_marked_processed`.

### B5. «Отписаться» при поданной заявке · низкий

Пользователь подал заявку и нажал «Отписаться». Бот отвечает «Вы не подписаны», а заявка остаётся в очереди
у администратора.

- Где: `TgSubscriptionService.unsubscribe`.
- Тест: `tests/tg/test_services.py::TestUnsubscribe::test_pending_user_is_not_subscribed`.

### B6. Разбор заявок прерывается при перезапуске · низкий

Данные FSM (id текущей заявки) хранятся в памяти. Если бот перезапустился во время разбора, кнопки
«Принять» / «Отклонить» ничего не делают и показывают «Новых заявок нет». Сама заявка не теряется,
её можно открыть заново.

- Где: `Dispatcher()` без хранилища (`tatd_bot/bot.py`), `tatd_bot/tg/handlers/admin.py`.
- Тест: `tests/tg/test_handlers.py::TestReviewApplications::test_accept_without_application_in_state`.

### B7. Имена авторов не обновляются до перезапуска · низкий

`AuthorsRegistry` живёт весь процесс и проверяется раньше Redis. Если автор сменил имя или в первый раз
пришёл без имени, это не исправится до перезапуска. Registry только растёт.

- Где: `VkAuthorService._get_or_create_user` / `_get_or_create_group`, `tatd_bot/vk/registry.py`.
- Тест: `tests/vk/test_services.py::TestGetOrCreateAuthor::test_registry_wins_over_redis`.

### B8. Окно «7 дней» в часовом поясе контейнера · низкий

Свежесть поста считается по `date.today()` и `date.fromtimestamp` в часовом поясе контейнера (UTC), а даты
в сообщениях — по Москве. На границе суток пост может выпасть из окна на 3 часа раньше или позже.

- Где: `VkFeedService._get_recent_posts_with_comments`.
- Тест: нет.

### B9. Пользователь VK без поля `sex` роняет проход · низкий

`vk_to_vk_user_base_data` падает с `KeyError`, если в ответе `users.get` нет `sex` или у него неизвестное
значение. Сейчас поле всегда запрашивается, поэтому это скорее хрупкость.

- Где: `tatd_bot/vk/mappers.py`.
- Тест: `tests/vk/test_mappers.py::test_vk_user_without_known_sex_raises`.

### B10. Ошибки VK API не видны · средний

Любая ошибка VK API превращается в пустой ответ: сеть, таймаут, ошибка авторизации, превышение частоты
запросов (код 6). Для мониторинга такой проход выглядит как «новых комментариев нет». Ошибка
пишется только в лог, и если, например, протух токен, мониторинг молча перестаёт работать.

Решение владельца (бывший вопрос Q4):
- ошибку логировать и пропускать проход: досрочно его завершить, состояние не сохранять;
- уведомлять администратора в Telegram, если ошибка повторяется N проходов подряд, а при ошибке
  авторизации — сразу.

Это новая функциональность, отложена.

- Где: `VkApiService._make_vk_call` (`tatd_bot/vk/api.py`), `VkFeedService`, `tatd_bot/monitor.py`.
- Тесты: `tests/vk/test_api.py::TestRequest`.

## Вопросы

### Q1. Теряются ли ответы после 10-го в ветке?

`wall.getComments` вызывается с `thread_items_count=10`, остальные ответы не запрашиваются, даже если
`thread.count` больше. Если VK действительно отдаёт не больше 10, ответы с 11-го не придут никогда
(тогда это баг с высоким приоритетом). Проверить можно только на настоящих ответах VK, а токен работает
только с сервера.

- Тест: `tests/vk/test_services_feed.py::TestNewReplies::test_replies_are_taken_only_from_thread_items`.

### Q3. Бывает ли ответ без `reply_to_user`?

Сейчас у такого ответа адресатом становится `User(0)`, и id 0 уходит в `users.get`. Если в настоящих ответах
VK так бывает — это баг.

- Тесты: `tests/vk/test_services.py::TestMakeReply::test_reply_without_reply_to_user`,
  `tests/vk/test_services_feed.py::TestAuthorsNames::test_reply_without_reply_to_user_requests_user_zero`.
