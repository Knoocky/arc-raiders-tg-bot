# ARC Raiders Events Bot

## Maps Catalog Source

`/api/arc-raiders/maps` does not exist in MetaForge and is not used by this project.

`MetaForgeProvider.fetch_maps_catalog()` keeps the same provider contract, but the strategy stays internal to the provider layer:

- it first derives maps from documented MetaForge data such as the schedule
- then merges the result with a local fallback catalog of known maps
- the application layer does not know whether maps came from API-derived data or fallback data

This fallback remains isolated in the provider/adaptor layer until MetaForge exposes an official maps-list endpoint.

## Timezones

All event times remain stored internally in UTC.

User-facing text is converted only when formatting:

- if a chat has a saved timezone, the bot uses it
- if a chat timezone is unknown, the bot falls back to `UTC+5`

## Inline Menu

The bot now includes an inline menu on top of the existing slash commands.

- `/start` opens the main menu
- `/menu` opens the main menu from any chat
- the menu works in private chats and groups
- nested screens use inline buttons with `Назад` and `В меню`
- manual notification input is handled through a short FSM step and then returns to the menu

Supported menu scenarios:

- subscribe to an event and then choose a specific map or `Любая карта`
- unsubscribe from one active subscription or remove all subscriptions
- configure notification offsets with preset buttons, removal buttons, reset, or manual input
- open the full grouped schedule
- open the grouped schedule for one selected event
- show current subscriptions and notification offsets

The menu reuses the same business logic as `/events`, `/list`, `/watch`, `/unwatch`, and `/notify`.

This applies to `/events` output and notification messages. Relative text such as `через 42 мин` and `ещё 12 мин` is still calculated from UTC timestamps and does not depend on timezone display.

Telegram-бот на Python 3.12+ для отслеживания ивентов ARC Raiders. Проект построен на `aiogram 3`, `SQLAlchemy 2`, `PostgreSQL`, `Alembic`, `httpx` и `pydantic`.

## Возможности

- `/events` показывает ближайшие ивенты
- `/events map <map name>` фильтрует по карте
- `/events event <event name>` фильтрует по ивенту
- `/watch all`
- `/watch map <map name>`
- `/watch event <event name>`
- `/watch event <event name> | map <map name>`
- `/unwatch all`
- `/unwatch map <map name>`
- `/unwatch event <event name>`
- `/unwatch event <event name> | map <map name>`
- `/notify <minutes...>`
- `/notify add <minutes...>`
- `/notify remove <minutes...>`
- `/notify list`
- `/list`
- `/maps`
- `/events_catalog`
- `/help`

Команды принимают человекочитаемые имена. Для комбинированного ввода `event + map` обязателен разделитель `|`.

## Архитектура

Проект разбит на слои:

- `app/bot` - aiogram handlers, форматтеры и парсинг команд
- `app/application` - orchestration-сервисы
- `app/domain` - доменные модели и enum'ы
- `app/infrastructure` - providers, persistence, scheduler
- `app/common` - конфигурация, логирование и общие утилиты

## Локальный запуск

1. Установить Python 3.12+ и PostgreSQL.
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Подготовить переменные окружения:

```bash
set BOT_TOKEN=<telegram bot token>
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/arc_raiders_bot
```

Опционально можно переопределить:

- `LOG_LEVEL`
- `PROVIDER_BASE_URL`
- `PROVIDER_SCHEDULE_PATH`
- `PROVIDER_EVENTS_CATALOG_PATH`
- `CATALOGS_REFRESH_MINUTES`
- `SCHEDULE_REFRESH_MINUTES`
- `NOTIFICATION_POLL_SECONDS`

4. Применить миграции:

```bash
alembic upgrade head
```

5. Запустить бота:

```bash
python -m app.main
```

## Тесты

```bash
pytest
```

Unit-тесты покрывают:

- нормализацию lookup-текста
- resolver
- matching подписок
- notification window
- парсинг команд
- MetaForge provider

Integration-тесты покрывают:

- refresh каталогов
- refresh расписания
- создание и удаление подписок
- dispatch уведомлений
- защиту от дублей
