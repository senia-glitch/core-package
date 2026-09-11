# Примеры использования core-package

В этой папке два примера — они демонстрируют **разные способы** работы с пакетом.

## `main_example.py` — in-memory демо, без event-infra

Показывает минимальный сценарий без внешней инфраструктуры:

- своя реализация `IDatabase` в памяти,
- вызов `start_core(db=...)`,
- выполнение сценария через `run(...)`,
- просмотр метрик через `get_core_metrics()`.

Полезен, чтобы понять базовый API пакета, не устанавливая PostgreSQL.

**Запуск:**

```bash
python core_project/examples/main_example.py
```

## `main_with_event_infra_example.py` — связка с event-infra

Показывает, как подключить реальную БД через пакет `event-infra`:

- `start_infrastructure()` из event-infra поднимает `EventRouter` и применяет миграции,
- `start_core(router=router)` инициализирует ядро, оборачивая роутер в адаптер,
- сценарии автоматически работают с БД,
- в конце — `await router.shutdown()`.

**Требует:**

```bash
pip install event-infra
# или
pip install "core-package[event-infra]"
```

и выполнить `infra-init` в корне проекта (создаст `models.py`, `alembic/`, `.infra.env`).

**Запуск:**

```bash
python core_project/examples/main_with_event_infra_example.py
```

## Что выбрать

| Ситуация | Пример |
|---|---|
| Попробовать core-package без БД | `main_example.py` |
| Работать с реальной PostgreSQL | `main_with_event_infra_example.py` |
| Своя БД (не event-infra) | пишите свою реализацию `IDatabase` и передавайте в `start_core(db=...)` |

Подробности — в README пакета `core-package`.