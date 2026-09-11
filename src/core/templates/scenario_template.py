"""Пример сценария для core-package.

Этот файл демонстрирует, как создать собственный сценарий,
унаследовав BaseScenario и зарегистрировав его в реестре.
"""

from pydantic import BaseModel
from core import BaseScenario, IDatabase, ICache, ILogger, IMetrics
from core.exceptions import NotFoundError


# 1. Определите DTO для входных данных
class MyScenarioDTO(BaseModel):
    """DTO для моего сценария."""
    user_id: int
    name: str


# 2. Определите Response (результат)
class MyScenarioResponse(BaseModel):
    """Ответ моего сценария."""
    user_id: int
    greeting: str


# 3. Создайте класс сценария
class MyScenario(BaseScenario):
    """Пример сценария: приветствие пользователя по ID."""

    async def execute(self, dto: MyScenarioDTO) -> MyScenarioResponse:
        # Пример использования зависимостей:
        # - self._db – для работы с БД
        # - self._cache – для кеширования
        # - self._logger – для логирования
        # - self._metrics – для сбора метрик

        # Логируем начало выполнения
        if self._logger:
            await self._logger.info(f"Выполнение MyScenario для user_id={dto.user_id}")

        # Запрос к БД (пример)
        user = await self._db.read("users", dto.user_id)
        if not user:
            raise NotFoundError(f"User {dto.user_id} not found")

        # Кешируем результат (пример)
        if self._cache:
            cache_key = f"user_greeting:{dto.user_id}"
            await self._cache.set(cache_key, f"Hello, {user['name']}!", ttl=60)

        # Собираем метрику
        if self._metrics:
            await self._metrics.increment("my_scenario_executed", user_id=dto.user_id)

        return MyScenarioResponse(
            user_id=user["id"],
            greeting=f"Hello, {user['name']}!",
        )


# 4. Зарегистрируйте сценарий через декоратор @register_scenario("my_scenario").
#    Автозагрузка из пакета — через ScenarioRegistry.discover("my_project.scenarios"),
#    которая обычно вызывается внутри start_core(discover="my_project.scenarios").