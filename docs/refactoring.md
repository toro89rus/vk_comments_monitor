# План рефакторинга

Здесь правки, которые не меняют поведение бота: тесты проходят до и после без изменений (кроме импортов
при переносе модулей). Баги и решения о поведении — в [issues.md](issues.md).

Пока это список кандидатов без порядка. Порядок и разбивка на шаги — следующая задача.

## Блокировки

- Мониторинг работает в event loop бота, но ходит в VK (`requests`) и Redis (`redis.Redis`) синхронно.
  Пока идёт проход (до 10 с на каждый запрос VK), бот не отвечает пользователям. Перевод на `aiohttp` и
  `redis.asyncio` делает async и `Repository`, и все сервисы над ним. Как обрабатывать ошибки нового
  клиента VK, зависит от вопроса Q4 в [issues.md](issues.md).

## Структура

- `Repository` один на оба домена: разделить на хранилище tg (подписчики, заявки, `bot_user`) и vk
  (комментарии, кэш авторов).
- `VkCommentsMonitorService` — оркестрация vk → tg — лежит в `tg/services`. Вынести на уровень приложения.
- Лишняя вложенность пакетов: `tg/services/services.py`, `tg/models/models.py`, `tg/mappers/mappers.py`,
  `tg/keyboards/keyboards.py`, `tg/filters/filters.py`, `tg/states/states.py`.
- `VkMessageService._make_message_entity` ветвится по типу модели. Заменить на две функции для
  комментария и ответа.
- Опечатка `subsciption_service` в ключе диспетчера и аргументах хендлеров.
- `BotUserService.save_user_info` объявлен как возвращающий `BotUser`, но возвращает `None`.
- Порт Redis 6379 зашит в `Repository`: перенести в конфиг.
- `load_dotenv()` вызывается при импорте `tatd_bot.config`, и тесты прочитают `.env`, если он окажется
  рядом. Оставить загрузку только в `load_config()`.

## Мёртвый код

- `scripts/vk_comments_monitor.py` и цели `start-vk`, `cron-vk_monitor`, `start-ya_maps`, `cron-ya_maps`
  в `Makefile` (сначала закрыть вопрос Q2 в [issues.md](issues.md)).
- `Group.cache`, `User.cache`, закомментированные заготовки в `tatd_bot/vk/models.py`.
- Кнопка `Button.SUBS_LIST` без обработчика.
- `VkApiService.get_user_name` / `get_group_name` не используются.
- Миграции в `tatd_bot/vk/migrations/`: `001` и `002` не запускаются, `003`–`005` ходят в `localhost`
  без конфига, `004` пишет ключ, который код не читает. Они уже применены. Решить: удалить или перенести
  в архив, а для будущих миграций сделать общий запуск с конфигом и учётом применённых.

## Зависимости и окружение

- `telegram==0.0.1` — пустой пакет, в коде не используется: удалить.
- `dotenv` → `python-dotenv`.
- `requests` уйдёт вместе с переходом на `aiohttp`.
- Docker: `uv:latest` и `redis:latest` без зафиксированных версий. `make install` ставит dev-зависимости
  в образ: нужен `uv sync --no-dev`. Опечатки в `.dockerignore` (`.ruff_cahe/`, `.gitignore/`).
