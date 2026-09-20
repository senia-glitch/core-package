# core-package

Платформа для построения бизнес-сценариев с абстракциями и утилитами.

## Назначение

Пакет предоставляет:

- Интерфейсы для внешних зависимостей: БД, кеш, логгер, метрики.
- Базовый класс `BaseScenario` и реестр сценариев.
- Утилиты: безопасность (bcrypt, JWT), работа с датами, валидаторы.
- Встроенные реализации: `TTLCache` (алиасы `FIFOCache`, `InMemoryCache`), `ConsoleLogger`, `InMemoryMetrics`.
- CLI-команды `core-init` (инициализация) и `core-upgrade` (обновление).
- Опциональный адаптер к пакету `event-infra`.

Пакет **не привязан** к конкретной БД. Он предоставляет абстракции, а конкретные реализации (`IDatabase`, `ICache`, `ILogger`, `IMetrics`) пользователь либо подключает из `event-infra`, либо пишет сам.

## Возможности

- **Гексагональная архитектура** — чёткое разделение интерфейсов и реализаций.
- **Точка входа `start_core()`** — единый запуск ядра в вашем проекте.
- **Регистрация сценариев декоратором** — `@register_scenario("name", response=..., dto=...)`.
- **Автозагрузка сценариев** — `start_core(discover="my_project.scenarios")`.
- **Валидация на этапе импорта** — `__init_subclass__` проверяет наличие `execute(self, dto)`.
- **Валидация DTO в `run()`** — при передаче `dto=` при регистрации, `run()` проверяет тип входного объекта.
- **Гарантия Response-модели** — при передаче `response=` при регистрации, `run()` всегда возвращает инстанс этой модели.
- **Автоматический сбор метрик** — `@track_metrics` и `@tracked_scenario`.
- **Потокобезопасный in-memory кеш** с TTL и ограничением размера.
- **Расширяемая система ошибок** — `CoreError` с HTTP-статусами и кодами.
- **Гибкая конфигурация** — из `.core-package.env`, поиск вверх по дереву каталогов, поддержка `CORE_ENV_PATH`.

## Установка

```bash
# Только ядро
pip install git+https://github.com/senia-glitch/core-package.git

# Ядро + event-infra (опциональный extra)
pip install "core-package[event-infra] @ git+https://github.com/senia-glitch/core-package.git"
```

Пакеты **независимы**. `core-package` не тянет `event-infra` при обычной установке.

## Быстрый старт

### 1. Инициализация проекта

В корне вашего проекта:

```bash
core-init
```

Будут созданы:

- `.core-package.env` — конфигурация (JWT, bcrypt, логирование, метрики).
- `core_project/scenarios/`, `core_project/interfaces/`, `core_project/utils/` — папки для вашего кода.
- `core_project/examples/` — примеры.
- `pyproject.toml`, `README.md` — если их ещё нет.

Флаги: `--force` (перезаписать), `--target-dir` (имя папки для кода, по умолчанию `core_project`).

### 2. Опишите свой сценарий

В `core_project/scenarios/my_scenario.py`:

```python
from pydantic import BaseModel
from core import BaseScenario, register_scenario


class MyDTO(BaseModel):
    user_id: int
    name: str


class MyResponse(BaseModel):
    greeting: str


@register_scenario("greeting", response=MyResponse, dto=MyDTO)
class GreetingScenario(BaseScenario):
    async def execute(self, dto: MyDTO):
        user = await self._db.read("users", dto.user_id)
        return MyResponse(greeting=f"Hello, {user['name']}!")
```

Параметры `response` и `dto` при регистрации — опциональны. Если указаны:
- `dto` — `run()` проверит, что переданный объект является инстансом этого класса
- `response` — `run()` гарантированно вернёт инстанс этой модели (автоконвертация из `dict`)

При наследовании `BaseScenario` автоматически проверяется наличие метода `execute(self, dto)` — ошибка возникает на этапе импорта, а не при первом вызове.

### 3. Запустите из своей точки входа

```python
import asyncio
from core import start_core, run


async def main():
    await start_core(
        db=MyDatabase(),
        discover="core_project.scenarios",
    )

    result = await run("greeting", MyDTO(user_id=1, name="Alice"))
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

## Точка входа

`start_core()` — единственная функция, которая нужна для запуска ядра.

```python
async def start_core(
    router=None,              # EventRouter из event-infra (опционально)
    *,
    db=None,                  # своя реализация IDatabase
    cache=None,               # реализация ICache (по умолчанию InMemoryCache)
    logger=None,              # реализация ILogger (по умолчанию ConsoleLogger)
    metrics=None,             # реализация IMetrics (по умолчанию InMemoryMetrics)
    discover=None,            # dotted-имя пакета со сценариями
) -> None
```

**Обязательно** передать `router` **или** `db` — но не оба.

После запуска из любого модуля проекта доступны:

- `await run("scenario_name", dto)` — выполнить сценарий по имени.
- `get_scenario("scenario_name")` — экземпляр с внедрёнными зависимостями.
- `get_db()` / `get_cache()` / `get_logger()` / `get_core_metrics()` — активные зависимости.

### Повторная инициализация

Ядро — синглтон на процесс. Повторный `start_core()` бросит `RuntimeError`. Для тестов есть `reset_core()`:

```python
from core import start_core, reset_core

await start_core(db=db1)
# ...
reset_core()
await start_core(db=db2)
```

### Завершение работы

Для корректного завершения (graceful shutdown) используйте `shutdown_core()`:

```python
from core import shutdown_core

await shutdown_core()  # очищает кеш и сбрасывает состояние
```

## Связка с event-infra

`core-package` и `event-infra` — независимые пакеты. Первый — про сценарии и абстракции, второй — про работу с PostgreSQL. Связываются они **опционально** через адаптер `EventInfraDatabaseAdapter`, который живёт внутри `core.adapters.event_infra` и импортируется лениво.

### Установка

```bash
# Оба пакета через extra
pip install "core-package[event-infra] @ git+https://github.com/senia-glitch/core-package.git"

# Или раздельно
pip install git+https://github.com/senia-glitch/core-package.git
pip install git+https://github.com/senia-glitch/event-infra.git
```

### Использование

В `main.py`:

```python
from run_infrastructure import start_infrastructure   # event-infra
from core import start_core, run                      # core-package


async def main():
    # 1. Инфраструктура БД: миграции + EventRouter
    router = await start_infrastructure()

    try:
        # 2. Ядро с адаптером к event-infra
        await start_core(
            router=router,
            discover="core_project.scenarios",
        )

        # 3. Работа со сценариями
        result = await run("create_user", CreateUserDTO(name="Alice"))
        print(result)

    finally:
        # 4. Graceful shutdown инфраструктуры
        await router.shutdown()
```

**Порядок обязателен:** `start_infrastructure()` → `start_core(router=router)`.
`router` доступен только после запуска event-infra.

### Если event-infra не установлен

Пакет работает без него. Передайте свою реализацию `IDatabase`:

```python
await start_core(db=MyInMemoryDatabase())
```

`start_core()` **не подставляет in-memory БД по умолчанию** — это осознанное решение, чтобы поведение было предсказуемым. `cache`, `logger` и `metrics` получают in-memory реализации автоматически, если не переданы явно.

## CLI-команды

### `core-init`

Инициализирует проект: создаёт структуру папок, шаблоны, примеры и конфигурацию.

```bash
core-init [--force] [--target-dir core_project]
```

Что создаётся:

- `.core-package.env` — всегда в корне.
- `<target-dir>/scenarios/`, `interfaces/`, `utils/` — с `__init__.py` и `README.md`.
- `<target-dir>/examples/`:
  - `main_example.py` — in-memory демо без event-infra.
  - `main_with_event_infra_example.py` — связка с event-infra.
  - `example_scenario.py` — шаблон сценария.
  - `README.md` — пояснение к примерам.
- `pyproject.toml`, `README.md` — если отсутствуют.

### `core-upgrade`

Обновляет пакет до последней версии из GitHub.

```bash
core-upgrade
```

Что делает:

1. Загружает `pyproject.toml` из `main`-ветки репозитория.
2. Сравнивает удалённую версию с текущей (попарное сравнение кортежей).
3. Если удалённая версия новее — проверяет совместимость с вашей версией Python.
4. При несовместимости — задаёт вопрос yes/no перед продолжением.
5. Выполняет `pip install --upgrade git+https://github.com/senia-glitch/core-package.git`.

**Ключевой принцип:** пакет обновляется только в `site-packages`. Пользовательский код (app/, .env, pyproject.toml, роуты, схемы) остаётся нетронутым.

## Архитектура и компоненты

### Интерфейсы

Все интерфейсы — `Protocol`, не привязаны к реализациям.

- `IDatabase` — `create`, `read`, `update`, `delete`, `query`.
- `EventInfraDatabaseAdapter` также предоставляет deprecated `custom()` (обёртка над `query()`).
- `ICache` — `get`, `set`, `delete`, `clear`.
- `ILogger` — `debug`, `info`, `warning`, `error`, `critical`.
- `IMetrics` — `record`, `increment`.

### BaseScenario

```python
class MyScenario(BaseScenario):
    async def execute(self, dto):
        ...
```

`BaseScenario` — абстрактный класс (`ABC`). Конструктор: `db` (обязательно), `cache`, `logger`, `metrics` (опционально). Метрики **не** включаются автоматически — используйте декоратор.

### Регистрация сценариев

**Способ 1 — декоратор** (рекомендуется):

```python
from core import BaseScenario, register_scenario, tracked_scenario
from pydantic import BaseModel


class HelloDTO(BaseModel):
    name: str


class HelloResponse(BaseModel):
    message: str


@register_scenario("hello", response=HelloResponse, dto=HelloDTO)
@tracked_scenario("hello")
class HelloScenario(BaseScenario):
    async def execute(self, dto):
        return HelloResponse(message=f"Hello, {dto.name}!")
```

Параметры декоратора `@register_scenario`:
- `name` — уникальное имя сценария (обязательно)
- `response` — Pydantic-модель ответа (опционально). Если указана — `run()` конвертирует результат `execute()` в эту модель
- `dto` — Pydantic-модель входных данных (опционально). Если указана — `run()` проверяет тип DTO перед вызовом `execute()`

Декоратор срабатывает в момент импорта модуля. Чтобы модуль импортировался при старте приложения, используйте `discover`:

```python
await start_core(db=db, discover="app.scenarios")
```

`discover` обходит все `.py` внутри пакета (кроме начинающихся с `_`) и импортирует их. Ошибка в одном модуле не ломает загрузку остальных.

**Способ 2 — вручную:**

```python
from core import ScenarioRegistry
ScenarioRegistry.register("hello", HelloScenario, response=HelloResponse, dto=HelloDTO)
```

### Метаданные сценариев

После регистрации через `ScenarioRegistry` можно получить метаданные сценария:

```python
from core import ScenarioRegistry

entry = ScenarioRegistry.get_entry("hello")
entry.scenario_cls  # класс сценария
entry.response      # Response-модель (или None)
entry.dto           # DTO-модель (или None)

# Или по отдельности:
ScenarioRegistry.get_response("hello")  # -> HelloResponse или None
ScenarioRegistry.get_dto("hello")       # -> HelloDTO или None
```

### Валидация в `run()`

Если при регистрации указан `dto`, функция `run()` проверяет тип перед вызовом `execute()`:

```python
await run("hello", HelloDTO(name="Alice"))   # OK
await run("hello", {"name": "Alice"})         # ValueError: ожидался DTO HelloDTO, получен dict
```

Если при регистрации указан `response`, `run()` гарантирует, что результат будет инстансом этой модели:

```python
# execute() вернул dict:
return {"message": "Hello!"}
# run() автоматически создаст HelloResponse(message="Hello!")

# execute() вернул другую Pydantic-модель:
return OtherModel(message="Hello!")
# run() сконвертирует через model_dump() → HelloResponse
```

### Исключения

- `CoreError` — базовое исключение (`code`, `http_status`).
- `NotFoundError` (HTTP 404).
- `ValidationError` (HTTP 422).
- `ConflictError` (HTTP 409).

```python
from core import NotFoundError
raise NotFoundError("User not found")
```

### DTO

`BaseDTO` — Pydantic-модель с общими полями:

- `access_token: Optional[str]`
- `limit: int = 100` (1..1000)
- `offset: int = 0`

### Утилиты

**Безопасность** (`core.utils.security`):

- `hash_password(password)` / `verify_password(password, hashed)` — bcrypt.
- `create_access_token(user_id, role, secret, expires_in)` / `create_refresh_token(...)` — JWT HS256.
- `decode_token(token, secret)` / `extract_token_info(token, secret)`.

**Даты** (`core.utils.datetime_utils`):

- `parse_iso_datetime(value)`
- `normalize_timezone(dt, offset_hours)`
- `is_datetime_in_past(dt, now=None)`
- `format_iso(dt, with_timezone=False)`

**Валидаторы** (`core.utils.validators`):

- `validate_pagination(limit, offset)`
- `validate_required(value, field_name)`
- `validate_email(email)`

### Встроенные реализации

**Логирование.** `ConsoleLogger` — пишет в stdout или файл. Уровень устанавливается при инициализации из `CORE_LOG_LEVEL`. Handler добавляется один раз.

**Метрики.** `InMemoryMetrics` — calls, errors, total/min/max/avg по каждому сценарию. Потокобезопасен (`asyncio.Lock`). Глобальный синглтон `get_metrics()` или свой экземпляр. Отключается через `CORE_METRICS_ENABLED=false`.

**Кеш.** `TTLCache` (алиасы `FIFOCache`, `InMemoryCache`) — `asyncio.Lock`, TTL на элемент, вытеснение по времени истечения при переполнении.

```python
from core import TTLCache

cache = TTLCache(ttl_seconds=60, max_size=1000)
await cache.set("key", "value")
value = await cache.get("key")
```

## Конфигурация

Файл `.core-package.env` — поиск вверх по дереву от текущей директории. Можно указать явно через `CORE_ENV_PATH`.

| Переменная | Описание | По умолчанию |
|---|---|---|
| `CORE_JWT_SECRET` | Секрет для JWT. **Обязательно измените!** При дефолтном значении пакет выводит предупреждение. | `change-me-in-production` |
| `CORE_ACCESS_TOKEN_MINUTES` | Время жизни access-токена (мин) | `15` |
| `CORE_REFRESH_TOKEN_DAYS` | Время жизни refresh-токена (дни) | `30` |
| `CORE_BCRYPT_ROUNDS` | Раунды bcrypt | `12` |
| `CORE_METRICS_ENABLED` | Включить метрики | `true` |
| `CORE_LOG_LEVEL` | Уровень логирования | `INFO` |
| `CORE_LOG_FILE` | Путь к файлу лога (пусто — stdout) | пусто |
| `CORE_ENV_PATH` | Явный путь к `.core-package.env` | пусто |
| `CORE_ENV` | Режим окружения (`production` включает проверку JWT) | пусто |
| `CORE_SKIP_DOTENV` | Пропустить загрузку `.core-package.env` (`true/1/yes`) | пусто |

## Расширение

### Свой сценарий

1. Унаследуйте `BaseScenario`.
2. Реализуйте `async def execute(self, dto)`.
3. Пометьте `@register_scenario("имя")` и, при желании, `@tracked_scenario("имя")`.
4. Загрузите через `start_core(discover="my_project.scenarios")`.

### Своя реализация IDatabase

Реализуйте методы `create`/`read`/`update`/`delete`/`query`, передайте в `start_core(db=...)`.

Примеры в `core_project/examples/` после `core-init`.

### Свой адаптер

Если вы хотите работать не с event-infra, а с другой БД — напишите класс-наследник `IDatabase`. Модуль `core.adapters.event_infra` можно рассматривать как образец.

## Тестирование

```bash
pip install -e ".[test]"
pytest tests/ -v
```

## Лицензия

MIT