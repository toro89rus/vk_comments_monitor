# Архитектура

Описывает, как код устроен сейчас. Проблемы и планы — в `docs/` (см. конец файла). При изменении структуры — модулей, потоков данных,
схемы Redis — обновлять в том же коммите.

## Назначение

Telegram-бот для сотрудников театра (группа VK `tuldramteatr`). Раз в `VK_MONITOR_UPDATE_DELAY` секунд
(по умолчанию 300) бот проверяет посты группы за последние 7 дней. Новые комментарии и ответы в ветках
он рассылает подписчикам в Telegram. Подписка — по заявке, которую одобряет администратор.

## Стек

- Python 3.12, зависимости — `uv` (`pyproject.toml`, `uv.lock`).
- aiogram 3 — Telegram, long polling. FSM-хранилище по умолчанию, в памяти.
- Redis — всё состояние: подписчики, обработанные комментарии, кэш имён авторов VK.
  Клиент async (`redis.asyncio.Redis`), один на процесс, закрывается при остановке бота. Все методы
  хранилищ и сервисов над ними — `async`.
- VK API — `aiohttp`, async, версия API 5.199. Запросы к VK идут строго по одному (у VK лимит частоты):
  async нужен, чтобы проход мониторинга не блокировал бота, а не для параллельных запросов. Это закреплено
  тестом `TestVkRequestsAreSequential`. Сам клиент тоже пропускает запросы по одному (`asyncio.Lock`) и
  не чаще `VkConfig.request_interval` (0,35 с, меньше 3 запросов в секунду).
- petrovich — склонение имён авторов («Комментарий от Ивана Петрова»).
- Запуск — Docker Compose: контейнеры `tatd_bot` и `redis` (данные в volume `redis_data`).

## Структура

```
tatd_bot/
  bot.py              точка входа: собирает зависимости, запускает мониторинг и polling
  config/config.py    AppConfig из переменных окружения; load_config() подгружает .env
  logger.py           настройка корневого логгера
  monitor.py          VkCommentsMonitorService — цикл мониторинга vk → рассылка в tg
  redis_client.py     create_redis_client — клиент Redis из конфига, общий для обоих хранилищ
  utils/time_utils.py unix-время → datetime в Europe/Moscow
  vk/
    api.py            VkApiService — HTTP-вызовы VK API (одна aiohttp-сессия, закрывается при остановке бота)
    models.py         Group, User (со склонением), Comment, Reply, Post
    registry.py       AuthorsRegistry — кэш авторов в памяти процесса
    mappers.py        JSON VK → модели
    text_formatting.py фильтрация текста комментариев («спасибо», поздравления, пустые)
    services.py       VkAuthorService, VkMessageService, VkFeedService
    repository.py     VkRepository — Redis: обработанные комментарии, кэш авторов
  tg/
    handlers/user.py  /start, «Подписаться», «Отписаться»
    handlers/admin.py разбор заявок администратором
    services.py       TgSubscriptionService, BotUserService
    repository.py     TgRepository — Redis: подписчики, заявки, bot_user
    formatters.py     TgMessageFormatter — модели VK → текст сообщений
    models.py         BotUser, BotUserStatus
    mappers.py        aiogram User / Redis-хэш ↔ BotUser
    lexicon.py        тексты кнопок и сообщений
    keyboards.py      reply-клавиатуры
    filters.py        IsAdmin
    states.py         AdminStates (FSM)
```

Вне git (в `.gitignore`) лежит `ya_maps_monitor` — мониторинг отзывов на Яндекс Картах. Эта часть заморожена,
не развивается и здесь не описывается.

## Сборка зависимостей

Внедрения зависимостей через фреймворк нет. Всё собирается вручную в `bot.py: run_bot()`:

```
redis_client = create_redis_client(config.redis)
TgRepository(redis_client), VkRepository(redis_client)
VkApiService(config)
AuthorsRegistry()
VkAuthorService(registry, vk_repo)
VkMessageService(author_service, vk_repo)
VkFeedService(api, author_service, message_service, vk_repo)
VkCommentsMonitorService(config, tg_repo, bot, formatter, feed_service)
TgSubscriptionService(config, tg_repo)
BotUserService(tg_repo)
```

В хендлеры через `dp[...]` передаются `config`, `subscription_service` и `bot_user_service`.
Ключ в `dp` совпадает с именем аргумента хендлера, по нему aiogram и подставляет зависимость. Мониторинг
запускается `asyncio.create_task` в том же event loop, что и polling.

## Поток: мониторинг комментариев

`VkCommentsMonitorService.monitor()` — бесконечный цикл: проход, затем `asyncio.sleep(update_delay)`.
Исключения прохода логируются, цикл продолжается.

1. `VkFeedService.get_new_comments()`:
   1. `api.get_posts()` — 20 последних постов (`wall.get`). Остаются посты не старше 7 дней
      с `comments.count > 0`.
   2. Для каждого поста — `api.get_comments(post_id)`: до 100 комментариев верхнего уровня, в каждом
      до 10 ответов из ветки (`thread_items_count=10`).
   3. Каждый комментарий → `Comment` через `VkMessageService`:
      - `is_new` — в Redis нет отметки `is_processed`;
      - текст прогоняется через `format_comment_text`: пустой, «спасибо» и поздравления с днём рождения
        превращаются в `""`. Комментарий с поздравлением отбрасывается целиком, даже если в нём есть
        другой текст. Это намеренно: для мониторинга поздравления — спам.
   4. Ответы ветки: новые — с `id` больше сохранённого `last_reply_id`, и с непустым текстом после
      `format_reply_text` (тот же фильтр плюс удаление обращения `[id123|Имя], `).
   5. Комментарий попадает в выдачу, если он новый с непустым текстом или у него есть новые ответы
      (`Comment.has_new_activity`). Пост попадает, если в нём есть хотя бы один такой комментарий.
   6. Авторы. `VkAuthorService.get_or_create_author(id)`: `id < 0` — группа, иначе пользователь.
      Сначала ищется в `AuthorsRegistry`, затем в Redis, иначе создаётся пустой. Для авторов без имени
      делается пакетный запрос `users.get` / `groups.getById`, результат пишется в registry и Redis.
2. Рассылка `_notify_subscribers`: подписчикам параллельно (`asyncio.gather`), но не больше
   `MAX_CONCURRENT_SENDS` одновременно. Каждому по порядку: пост (HTML, ссылка и первые 100 символов),
   затем каждый комментарий, затем его ответы — отдельными сообщениями. Ошибки — по каждому подписчику
   отдельно, проход не прерывают:
   - `TelegramRetryAfter` — пауза `retry_after` и повтор того же сообщения, до `MAX_SEND_RETRIES` раз;
   - `TelegramForbiddenError` (бот заблокирован) — подписчик удаляется, статус `unsubscribed`;
   - другая ошибка Telegram (в том числе исчерпанные повторы) — в лог, остаток рассылки этому
     подписчику пропускается, он остаётся подписан.
3. `save_comments_cache`: новым комментариям ставится `is_processed`, комментариям с новыми ответами —
   `last_reply_id` = id последнего отправленного ответа.

Состояние «что уже отправлено» записывается после рассылки всем, в том числе если кому-то сообщения
не дошли: пропущенное этому подписчику не досылается, зато остальные не получают повтор. Если проход
упал посередине по другой причине (ошибка VK, Redis), в следующий раз всё отправится заново.

## Поток: подписка

Статусы `BotUser`: `new` → `pending` → `subscribed` / `rejected`; `subscribed` → `unsubscribed`.

1. `/start` — пользователь сохраняется в `bot_user:{id}` (если его ещё нет). Администратору показывается
   клавиатура `ADMIN_PANEL`, остальным `USER_SUBSCRIBE`.
2. «Подписаться» → `TgSubscriptionService.request_subscription`. Если пользователь уже подписан или уже
   ждёт — сообщение об этом. Иначе статус `pending`, id добавляется в `pending_subscribers`,
   администратору приходит «Заявка от …».
3. Администратор: «Обработать заявки» → FSM-состояние `reviewing_applications`. Заявки показываются
   по одной, в порядке подачи, с кнопками «Принять» / «Отклонить». Пользователю приходит результат.
   id текущей заявки хранится в данных FSM (в памяти).
4. «Отписаться» — удаление из `subscribers`, статус `unsubscribed`, уведомление администратору.

Администратор один, `ADMIN_ID` из окружения. Фильтр `IsAdmin` сравнивает `from_user.id`.

## Схема Redis

| Ключ | Тип | Поля / значение | TTL | Пишет | Читает |
|---|---|---|---|---|---|
| `subscribers` | set | tg user id | — | подписка, блокировка бота | рассылка |
| `pending_subscribers` | zset | tg user id, score = время заявки | — | подписка | админ |
| `bot_user:{tg_id}` | hash | `full_name`, `username`, `status` | — | хендлеры, подписка | хендлеры, админ |
| `comment:{vk_comment_id}` | hash | `is_processed` = `1`, `last_reply_id` | 8 дней | мониторинг | мониторинг |
| `user:{vk_user_id}` | hash | `first_name`, `last_name`, `gender` (значение petrovich `Gender` или `""`) | 30 дней | кэш авторов | кэш авторов |
| `group:{vk_group_id}:name` | hash | `name` | 30 дней | кэш авторов | кэш авторов |

TTL комментариев (8 дней) больше окна мониторинга (7 дней). Поэтому отметка о старом комментарии
не пропадает, пока пост ещё проверяется.

## Миграции

Миграций в коде сейчас нет. Прежние разовые скрипты `001`–`005` уже применены и удалены, они остались
в истории git (последний коммит с ними — `c5a21ea`). Учёта применённых миграций нет. Новая миграция —
`tatd_bot/vk/migrations/redis_migration_006*.py`. Общий запуск с конфигом и учётом применённых
делается отдельной задачей, вместе с первой новой миграцией.

## Конфигурация

Переменные окружения (`.env`): `TG_TOKEN`, `ADMIN_ID`, `VK_TOKEN`, `VK_GROUP_ID` (по умолчанию
`-48164678`), `VK_GROUP_NAME`, `VK_MONITOR_UPDATE_DELAY`, `REDIS` (хост), `REDIS_PORT` (по умолчанию
6379), `ENV` (`DEV` — уровень логов DEBUG). Форматы дат — константы в `config.py`.

## Запуск и деплой

- Работает только на сервере через Docker Compose. Локально проект не запускается: нет локального окружения
  и тестовых токенов.
- В контейнере: `make run` → `tatd_bot.bot`. Это один долгоживущий процесс: polling бота плюс бесконечный
  цикл мониторинга. Образ — `python:3.12-slim-trixie` + `uv` 0.5.13 (как в CI),
  зависимости ставятся отдельным слоем до копирования кода. `redis:8.10.1`: версия зафиксирована,
  менять только на более новую (старый Redis может не прочитать файл данных нового).
- Деплой: `deploy.sh` на сервере (`/home/toro/vk_comments_monitor`) по крону. Если `origin/main` ушёл
  вперёд — `git pull` и `docker compose up -d --build tatd_bot`. Пуш в `main` = деплой.
- Проверки: `make check` — `ruff format --check`, `ruff check`, `pytest` (по отдельности: `make format`,
  `make lint`, `make test`). Тесты — `tests/` (pytest, pytest-asyncio в режиме auto, fakeredis).
  Старые нарушения правил ruff помечены `# noqa`.
- CI: `.github/workflows/check.yml` — `make check` на каждый PR в `main` и на каждый пуш в `main`
  (job `check`). `main` защищён на GitHub (ruleset): мерж только через PR с зелёным `check`, без
  force push и удаления. Сам `deploy.sh` результат CI не проверяет.
- `make install` (= `uv sync`) — локальная установка вместе с dev-зависимостями. В Docker-образ ставятся
  только основные (`uv sync --locked --no-dev`), и `make run` запускает бота с `--no-dev`, чтобы `uv run`
  не доустанавливал dev-группу при старте контейнера.

## Проблемы и планы

- Баги и открытые вопросы — [docs/issues.md](docs/issues.md).
- Структурные правки без смены поведения — [docs/refactoring.md](docs/refactoring.md).
