# core-package

Платформа для построения бизнес-сценариев с абстракциями и утилитами.

## Назначение

Пакет предоставляет:

- Интерфейсы для внешних зависимостей (БД, кеш, логирование, метрики)
- Базовый класс для сценариев и реестр сценариев
- Утилиты: безопасность (bcrypt, JWT), работа с датами, валидаторы
- Встроенные логгер и метрики в памяти
- CLI-команду `core-init` для быстрой инициализации проекта

## Возможности

- **Гексагональная архитектура** — чёткое разделение интерфейсов и реализаций.
- **Автоматический сбор метрик** — декораторы `@track_metrics` и `@tracked_scenario`.
- **Регистрация сценариев декоратором** — `@register_scenario("name")`.
- **Автозагрузка сценариев из пакета** — `ScenarioRegistry.discover("app.scenarios")`.
- **Потокобезопасный in-memory кэш** с TTL и ограничением размера.
- **Расширяемая система ошибок** — базовый `CoreError` с HTTP-статусами и кодами.
- **Гибкая конфигурация** — загрузка из `.core-package.env`, поиск вверх по дереву каталогов, поддержка `CORE_ENV_PATH`.

## Быстрый старт

1. Установите пакет:

   ```bash
   pip install git+https://github.com/ваш-username/core-package.git
Инициализируйте проект:

bash
core-init
Будут созданы:

.core-package.env — файл с переменными окружения

scenarios/, interfaces/, utils/ — папки для вашего кода

examples/ — примеры использования

pyproject.toml, README.md — если их ещё нет

Создайте сценарий, унаследовав BaseScenario и пометив его @register_scenario.

Запустите пример:

bash
python examples/main_example.py
Архитектура
Пакет построен по принципам гексагональной архитектуры:

Интерфейсы (core.interfaces) — абстракции для БД, кеша, логгера и метрик.

Базовый сценарий (BaseScenario) — основа для всех бизнес-сценариев.

Реестр сценариев (ScenarioRegistry) — регистрация и получение сценариев по имени.

Утилиты (core.utils) — чистые функции: безопасность, даты, валидация.

Компоненты
Интерфейсы
IDatabase — асинхронные CRUD-операции и произвольные SQL-запросы.

ICache — асинхронное кеширование (get, set, delete, clear).

ILogger — асинхронное логирование (debug, info, warning, error, critical).

IMetrics — асинхронный сбор метрик (record, increment).

Все интерфейсы определены через Protocol и не зависят от конкретных реализаций.

BaseScenario
python
from core import BaseScenario

class MyScenario(BaseScenario):
    async def execute(self, dto):
        # логика сценария
        pass
Конструктор принимает:

db — обязательный экземпляр IDatabase

cache — опционально ICache

logger — опционально ILogger

metrics — опционально IMetrics

Регистрация сценариев
Способ 1 — декоратор (рекомендуется):

python
from core import BaseScenario, register_scenario, tracked_scenario

@register_scenario("hello")
@tracked_scenario("hello")
class HelloScenario(BaseScenario):
    async def execute(self, dto):
        return {"message": f"Hello, {dto.name}!"}
Декоратор срабатывает в момент импорта модуля. Чтобы модуль импортировался
при старте приложения, вызовите один раз:

python
from core import ScenarioRegistry

ScenarioRegistry.discover("app.scenarios")
discover обходит все .py файлы внутри указанного пакета (кроме тех,
что начинаются с _), импортирует их — и все сценарии с @register_scenario
оказываются зарегистрированы.

Способ 2 — ручная регистрация:

python
from core import ScenarioRegistry

ScenarioRegistry.register("hello", HelloScenario)
Используйте, если нужно зарегистрировать сценарий не в момент импорта модуля,
а программно.

Получение сценария:

python
scenario = ScenarioRegistry.get("hello", deps={"db": db, "logger": logger})
result = await scenario.execute(dto)
Исключения
Иерархия исключений:

CoreError — базовое исключение с опциональными атрибутами code и http_status.

NotFoundError (HTTP 404)

ValidationError (HTTP 422)

ConflictError (HTTP 409)

python
from core import NotFoundError

raise NotFoundError("User not found")
DTO
Базовый класс BaseDTO (Pydantic) с общими полями:

access_token: Optional[str]

limit: int = 100 (от 1 до 1000)

offset: int = 0

Утилиты
Безопасность (core.utils.security)
hash_password(password) -> str — bcrypt-хеширование.

verify_password(password, hashed) -> bool

create_access_token(user_id, role, secret, expires_in) -> str — JWT HS256.

create_refresh_token(user_id, secret, expires_in) -> str

decode_token(token, secret) -> dict

extract_token_info(token, secret) -> TokenInfo

Работа с датами (core.utils.datetime_utils)
parse_iso_datetime(value) -> datetime

normalize_timezone(dt, offset_hours) -> datetime

is_datetime_in_past(dt) -> bool

format_iso(dt, with_timezone=False) -> str

Валидаторы (core.utils.validators)
validate_pagination(limit, offset)

validate_required(value, field_name)

validate_email(email)

Встроенные реализации
Логирование
ConsoleLogger — реализация ILogger, пишет в stdout или файл.

Уровень: CORE_LOG_LEVEL (по умолчанию INFO).

Файл: если задан CORE_LOG_FILE, вывод пишется в файл.

Обработчик добавляется один раз, чтобы избежать дублирования.

Метрики
InMemoryMetrics — хранит статистику в памяти.

Доступ через get_metrics() (глобальный синглтон) или собственный экземпляр.

Собирает: количество вызовов, ошибки, среднее/минимальное/максимальное время.

Включение/отключение: CORE_METRICS_ENABLED (по умолчанию true).

Кэш
InMemoryCache — потокобезопасная реализация ICache с TTL и ограничением размера.

python
from core import InMemoryCache

cache = InMemoryCache(ttl_seconds=60, max_size=1000)
await cache.set("key", "value")
value = await cache.get("key")
CLI-команда core-init
Инициализирует проект, создавая структуру и файлы.

--force — перезаписать существующие файлы.

--target-dir — имя папки для кода (по умолчанию core_project).

Создаваемые файлы:

.core-package.env

scenarios/, interfaces/, utils/ с __init__.py и README

examples/example_scenario.py, examples/event_infra_adapter.py, examples/main_example.py

pyproject.toml (если отсутствует)

README.md (если отсутствует)

Конфигурация
Пакет загружает настройки из .core-package.env (поиск вверх по дереву каталогов)
или из переменных окружения.

Переменная	Описание	По умолчанию
CORE_JWT_SECRET	Секрет для JWT	change-me-in-production
CORE_ACCESS_TOKEN_MINUTES	Время жизни access-токена (мин)	15
CORE_REFRESH_TOKEN_DAYS	Время жизни refresh-токена (дни)	30
CORE_BCRYPT_ROUNDS	Раунды bcrypt	12
CORE_METRICS_ENABLED	Включить метрики (true/false)	true
CORE_LOG_LEVEL	Уровень логирования	INFO
CORE_LOG_FILE	Путь к файлу лога (пусто — stdout)	(пусто)
CORE_ENV_PATH	Явный путь к файлу .env	(пусто)
Пример адаптера для event-infra
python
from core.interfaces import IDatabase

class EventInfraDatabaseAdapter(IDatabase):
    def __init__(self, router):
        self._router = router

    async def create(self, entity, data):
        resp = await self._router.create(entity, data, channel="write")
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.data[0]

    async def read(self, entity, id):
        resp = await self._router.read(entity, id, channel="read")
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.data[0] if resp.data else None

    async def update(self, entity, id, data):
        resp = await self._router.update(entity, id, data, channel="write")
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.data[0]

    async def delete(self, entity, id):
        resp = await self._router.delete(entity, id, channel="write")
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.count > 0

    async def custom(self, sql, params):
        resp = await self._router.custom(sql, params, channel="read")
        if not resp.success:
            raise Exception(resp.error.message)
        return [dict(row._mapping) for row in resp.data if row]
Расширение
Создайте класс, унаследовав BaseScenario.

Реализуйте метод execute(dto).

Помечайте класс декоратором @register_scenario("имя").

В точке входа приложения вызовите ScenarioRegistry.discover("app.scenarios").

python
from core import BaseScenario, register_scenario, tracked_scenario

@register_scenario("my_scenario")
@tracked_scenario("my_scenario")
class MyScenario(BaseScenario):
    async def execute(self, dto):
        return {"ok": True}
Тестирование
bash
pytest tests/ -v
Лицензия
MIT