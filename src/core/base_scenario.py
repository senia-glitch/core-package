# src/core/base_scenario.py
"""Базовый класс для всех бизнес-сценариев."""

from typing import Any, Optional
from .interfaces import IDatabase, ICache, ILogger, IMetrics


class BaseScenario:
    """Абстрактный базовый класс для сценариев.

    Сценарий получает зависимости через конструктор и реализует метод execute.
    Для сбора метрик используйте декоратор @track_metrics над методом execute
    или @tracked_scenario над классом.
    """

    def __init__(
        self,
        db: IDatabase,
        cache: Optional[ICache] = None,
        logger: Optional[ILogger] = None,
        metrics: Optional[IMetrics] = None,
    ):
        self._db = db
        self._cache = cache
        self._logger = logger
        self._metrics = metrics

    async def execute(self, dto: Any) -> Any:
        raise NotImplementedError("Метод execute должен быть переопределён")