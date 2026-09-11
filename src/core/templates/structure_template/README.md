# Структура проекта для core-package

Это базовая структура, создаваемая командой `core-init`.

- `scenarios/` — ваши сценарии (наследники `BaseScenario`).
- `interfaces/` — реализации интерфейсов (адаптеры) для вашей инфраструктуры.
- `utils/` — ваши дополнительные утилиты.

## Как это использовать

1. Опишите свои сценарии в `scenarios/` — классы-наследники `BaseScenario`.
2. Пометьте каждый сценарий декоратором `@register_scenario("имя")`.
3. В точке входа приложения вызовите `start_core(..., discover="<пакет>.scenarios")` —
   все модули внутри `scenarios/` будут импортированы, и декораторы сработают.

Пример:

```python
from core import start_core, run

async def main():
    await start_core(discover="core_project.scenarios")

    result = await run("my_scenario", MyDTO(...))
    print(result)
```

Если нужна связка с event-infra — передайте `router` в `start_core(router=router)`.
Подробности — в README пакета.