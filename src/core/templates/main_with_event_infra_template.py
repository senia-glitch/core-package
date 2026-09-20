# templates/main_with_event_infra_template.py
"""Пример связки core-package с event-infra.

Демонстрирует:
- Запуск инфраструктуры через start_infrastructure() (event-infra)
- Инициализацию ядра через start_core(router=...) (core-package)
- Автозагрузку сценариев через discover
- Вызов сценариев через run(...)
- Graceful shutdown event-infra

Требует:
    pip install event-infra (или core-package[event-infra])
    Запуск infra-init в корне проекта (создаёт models.py, alembic/, .infra.env)

Запуск:
    python examples/main_with_event_infra_example.py
"""

import asyncio

# Импорт event-infra: модуль run_infrastructure создаётся командой infra-init
from run_infrastructure import start_infrastructure

from core import start_core, run, shutdown_core
from pydantic import BaseModel


class GreetingDTO(BaseModel):
    user_id: int
    name: str


async def main():
    print("=" * 60)
    print("ЗАПУСК СВЯЗКИ core-package + event-infra")
    print("=" * 60)

    # 1. Поднимаем event-infra (миграции + EventRouter)
    print("\n[1/3] Запуск event-infra...")
    router = await start_infrastructure()
    print("      EventRouter готов.")

    try:
        # 2. Инициализируем ядро, передавая роутер через адаптер
        print("\n[2/3] Запуск core-package...")
        await start_core(
            router=router,
            discover="core_project.scenarios",  # путь к вашим сценариям
        )
        print("      Ядро готово.")

        # 3. Выполняем сценарий
        print("\n[3/3] Выполнение сценария 'greeting'...")
        dto = GreetingDTO(user_id=1, name="Alice")
        result = await run("greeting", dto)
        print(f"      Ответ: {result}")

    finally:
        # 4. Корректное завершение
        print("\nОстановка core-package...")
        await shutdown_core()
        print("Остановка event-infra...")
        await router.shutdown()
        print("Готово.")


if __name__ == "__main__":
    asyncio.run(main())