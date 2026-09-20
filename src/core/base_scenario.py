# src/core/base_scenario.py
"""Базовый класс для всех бизнес-сценариев."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from .interfaces import IDatabase, ICache, ILogger, IMetrics


class BaseScenario(ABC):
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

    @abstractmethod
    async def execute(self, dto: Any) -> Any:
        ...