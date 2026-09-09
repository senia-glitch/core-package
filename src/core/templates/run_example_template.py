# templates/run_example_template.py
"""Пример использования core-package с in-memory заглушкой БД.

Демонстрирует:
- Создание in-memory адаптера IDatabase
- Использование встроенных логгера и метрик
- Регистрацию и выполнение сценария
- Вывод метрик после выполнения

Запуск:
    python examples/run_example.py
"""

import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from core import (
    BaseScenario,
    IDatabase,
    ScenarioRegistry,
    ConsoleLogger,
    InMemoryMetrics,
    track_metrics,
)
from core.exceptions import NotFoundError


# ============================================================
# 1. ЗАГЛУШКА БАЗЫ ДАННЫХ (IN-MEMORY)
# ============================================================

class InMemoryDatabase(IDatabase):
    """Простая in-memory реализация IDatabase для демонстрации."""

    def __init__(self):
        self._data: Dict[str, Dict[int, Dict[str, Any]]] = {}
        self._counters: Dict[str, int] = {}

    async def create(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if entity not in self._data:
            self._data[entity] = {}
            self._counters[entity] = 0
        self._counters[entity] += 1
        record = {"id": self._counters[entity], **data}
        self._data[entity][record["id"]] = record
        return record

    async def read(self, entity: str, id: Any) -> Optional[Dict[str, Any]]:
        return self._data.get(entity, {}).get(id)

    async def update(self, entity: str, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        if entity not in self._data or id not in self._data[entity]:
            raise NotFoundError(f"Record {id} not found in {entity}")
        self._data[entity][id].update(data)
        return self._data[entity][id]

    async def delete(self, entity: str, id: Any) -> bool:
        if entity in self._data and id in self._data[entity]:
            del self._data[entity][id]
            return True
        return False

    async def custom(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Упрощённая имитация – возвращаем все записи таблицы
        parts = sql.lower().split("from")
        if len(parts) > 1:
            table = parts[1].strip().split()[0]
            if table in self._data:
                return list(self._data[table].values())
        return []


# ============================================================
# 2. ОПРЕДЕЛЕНИЕ СЦЕНАРИЯ
# ============================================================

class GreetingDTO(BaseModel):
    user_id: int
    name: str


class GreetingResponse(BaseModel):
    user_id: int
    greeting: str


class GreetingScenario(BaseScenario):
    """Пример сценария: приветствие пользователя."""

    @track_metrics("greeting_scenario")
    async def execute(self, dto: GreetingDTO) -> GreetingResponse:
        if self._logger:
            await self._logger.info(f"Выполнение GreetingScenario для user_id={dto.user_id}")

        user = await self._db.read("users", dto.user_id)
        if not user:
            user = await self._db.create("users", {"id": dto.user_id, "name": dto.name})
            if self._logger:
                await self._logger.info(f"Создан пользователь: {user}")

        if self._cache:
            await self._cache.set(f"greeting:{dto.user_id}", f"Hello, {user['name']}!", ttl=60)

        if self._metrics:
            await self._metrics.increment("greeting_calls", user_id=dto.user_id)

        return GreetingResponse(user_id=user["id"], greeting=f"Hello, {user['name']}!")


# ============================================================
# 3. ЗАПУСК
# ============================================================

async def main():
    print("=" * 50)
    print("ЗАПУСК ПРИМЕРА core-package")
    print("=" * 50)

    # 1. Создаём зависимости
    db = InMemoryDatabase()
    logger = ConsoleLogger()
    metrics = InMemoryMetrics()

    # 2. Регистрируем сценарий
    ScenarioRegistry.register("greeting", GreetingScenario)

    # 3. Получаем экземпляр сценария
    deps = {"db": db, "logger": logger, "metrics": metrics}
    scenario = ScenarioRegistry.get("greeting", deps)

    # 4. Выполняем сценарий несколько раз
    dto = GreetingDTO(user_id=42, name="Alice")
    print(f"\nВызов с user_id={dto.user_id}, name={dto.name}")
    response = await scenario.execute(dto)
    print(f"Ответ: {response.greeting}")

    dto2 = GreetingDTO(user_id=100, name="Bob")
    print(f"\nВызов с user_id={dto2.user_id}, name={dto2.name}")
    response2 = await scenario.execute(dto2)
    print(f"Ответ: {response2.greeting}")

    # 5. Выводим метрики
    print("\n" + "=" * 50)
    print("МЕТРИКИ ВЫПОЛНЕНИЯ")
    print("=" * 50)
    stats = metrics.get_stats()
    for s in stats:
        print(f"  {s.name}:")
        print(f"    Вызовов: {s.calls}")
        print(f"    Ошибок: {s.errors}")
        print(f"    Среднее время: {s.avg_time_ms:.2f} мс")
        print(f"    Мин. время: {s.min_time_ms:.2f} мс")
        print(f"    Макс. время: {s.max_time_ms:.2f} мс")

    print("\nПример успешно выполнен.")


if __name__ == "__main__":
    asyncio.run(main())