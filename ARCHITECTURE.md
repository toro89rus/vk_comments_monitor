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
  Клиент синхронный (`redis.Redis`).
- VK API — `requests`, синхронно, версия API 5.199.
- petrovich — склонение имён авторов («Комментарий от Ивана Петрова»).
- Запуск — Docker Compose: контейнеры `tatd_bot` и `redis` (данные в volume `redis_data`).

## Структура

```
tatd_bot/
  bot.py              точка входа: собирает зависимости, запускает мониторинг и polling
  config/config.py    AppConfig из переменных окружения (.env через dotenv)
  logger.py           настройка корневого логгера
  repository.py       Repository — весь доступ к Redis (и для tg, и для vk)
  utils/time_utils.py unix-время → datetime в Europe/Moscow
  vk/
    api.py            VkApiService — HTTP-вызовы VK API
    models.py         Group, User (со склонением), Comment, Reply, Post
    registry.py       AuthorsRegistry — кэш авторов в памяти процесса
    mappers.py        JSON VK → модели
    text_formatting.py фильтрация текста комментариев («спасибо», поздравления, пустые)
    services.py       VkAuthorService, VkMessageService, VkFeedService
    migrations/       разовые скрипты миграции данных Redis
  tg/
    handlers/user.py  /start, «Подписаться», «Отписаться»
    handlers/admin.py разбор заявок администратором
    services/services.py VkCommentsMonitorService (цикл мониторинга и рассылка),
                      TgSubscriptionService, BotUserService
    formatters.py     TgMessageFormatter — модели VK → текст сообщений
    models/models.py  BotUser, BotUserStatus
    mappers/mappers.py aiogram User / Redis-хэш ↔ BotUser
    lexicon.py        тексты кнопок и сообщений
    keyboards/        reply-клавиатуры
    filters/          IsAdmin
    states/           AdminStates (FSM)
scripts/vk_comments_monitor.py  остаток прежней схемы: разовый прогон мониторинга по крону
                                (дублирует VkCommentsMonitorService, сейчас не используется)
```

Вне git (в `.gitignore`) лежит `ya_maps_monitor` — мониторинг отзывов на Яндекс Картах. Эта часть заморожена,
не развивается и здесь не описывается.

## Сборка зависимостей

Внедрения зависимостей через фреймворк нет. Всё собирается вручную в `bot.py: run_bot()`:

```
Repository(redis_host)
VkApiService(config)
AuthorsRegistry()
VkAuthorService(registry, repo)
VkMessageService(author_service, repo)
VkFeedService(api, author_service, message_service, repo)
VkCommentsMonitorService(config, repo, bot, formatter, feed_service)
TgSubscriptionService(config, repo)
BotUserService(repo)
```

В хендлеры через `dp[...]` передаются `config`, `repo`, `subscription_service` и
`bot_user_service`. Ключ в `dp` совпадает с именем аргумента хендлера, по нему aiogram и подставляет
зависимость. Мониторинг запускается `asyncio.create_task`
в том же event loop, что и polling.

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
2. Рассылка `_notify_subscribers`: всем подписчикам параллельно (`asyncio.gather`). Каждому по порядку:
   пост (HTML, ссылка и первые 100 символов), затем каждый комментарий, затем его ответы — отдельными
   сообщениями. `TelegramForbiddenError` (бот заблокирован) — подписчик удаляется, статус `unsubscribed`.
3. `save_comments_cache`: новым комментариям ставится `is_processed`, комментариям с новыми ответами —
   `last_reply_id` = id последнего отправленного ответа.

Состояние «что уже отправлено» записывается только после рассылки всем. Если проход упал посередине,
в следующий раз всё отправится заново.

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

`tatd_bot/vk/migrations/` — разовые скрипты, запускались вручную. Учёта применённых миграций нет.
`redis_migration_001*` и `002` в текущем виде не запускаются: они импортируют уже несуществующие
`repository.r` и `tatd_bot.logger.logger`. `003`–`005` ходят в Redis на `localhost`, без конфига.
`004` пишет ключ `group:{id}`, а код читает `group:{id}:name`. Схема ключей менялась после миграции.

## Конфигурация

Переменные окружения (`.env`): `TG_TOKEN`, `ADMIN_ID`, `VK_TOKEN`, `VK_GROUP_ID` (по умолчанию
`-48164678`), `VK_GROUP_NAME`, `VK_MONITOR_UPDATE_DELAY`, `REDIS` (хост), `ENV` (`DEV` — уровень логов DEBUG).
Порт Redis 6379 зашит в `Repository`. Форматы дат — константы в `config.py`.

## Запуск и деплой

- Работает только на сервере через Docker Compose. Локально проект не запускается: нет локального окружения
  и тестовых токенов.
- В контейнере: `make run` → `tatd_bot.bot`. Это один долгоживущий процесс: polling бота плюс бесконечный
  цикл мониторинга. Образ — `python:3.12-slim-trixie` + `uv:latest`. `redis:latest` без
  фиксации версии.
- Деплой: `deploy.sh` на сервере (`/home/toro/vk_comments_monitor`) по крону. Если `origin/main` ушёл
  вперёд — `git pull` и `docker compose up -d --build tatd_bot`. Пуш в `main` = деплой.
- `make start-vk` / `cron-vk_monitor` запускают `scripts/vk_comments_monitor.py` — остаток схемы до
  перехода на aiogram 3 (`f2d8b18`), когда мониторинг запускался по крону. Compose его не вызывает.
  Цели `start-ya_maps` / `cron-ya_maps` ссылаются на модуль, которого нет в git.
- Проверки: `make check` — `ruff format --check`, `ruff check`, `pytest` (по отдельности: `make format`,
  `make lint`, `make test`). Тесты — `tests/` (pytest, pytest-asyncio в режиме auto, fakeredis).
  Старые нарушения правил ruff помечены `# noqa`.
- CI: `.github/workflows/check.yml` — `make check` на каждый PR в `main` и на каждый пуш в `main`
  (job `check`). Деплой от CI пока не зависит: `deploy.sh` подтягивает `main`, не глядя на результат.
- `make install` (= `uv sync`) ставит и dev-зависимости, в том числе в Docker-образ.

## Проблемы и планы

- Баги и открытые вопросы — [docs/issues.md](docs/issues.md).
- Структурные правки без смены поведения — [docs/refactoring.md](docs/refactoring.md).
