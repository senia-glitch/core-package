# src/core/metrics.py
"""Встроенная реализация IMetrics для хранения метрик в памяти."""

import time
from typing import Dict, List, Optional
from .interfaces.metrics import IMetrics
from .config import get_env_bool


class ScenarioStats:
    """Статистика выполнения одного сценария."""

    def __init__(self, name: str):
        self.name = name
        self.calls = 0
        self.errors = 0
        self.total_time_ms = 0.0
        self.min_time_ms = float("inf")
        self.max_time_ms = 0.0

    def record(self, elapsed_ms: float, error: bool = False):
        self.calls += 1
        if error:
            self.errors += 1
        self.total_time_ms += elapsed_ms
        if elapsed_ms < self.min_time_ms:
            self.min_time_ms = elapsed_ms
        if elapsed_ms > self.max_time_ms:
            self.max_time_ms = elapsed_ms

    @property
    def avg_time_ms(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.total_time_ms / self.calls


class InMemoryMetrics(IMetrics):
    """Реализация IMetrics с хранением метрик в памяти."""

    def __init__(self):
        self._stats: Dict[str, ScenarioStats] = {}
        self._enabled = get_env_bool("CORE_METRICS_ENABLED", True)

    async def record(self, name: str, value: float, **labels) -> None:
        """Записывает числовое значение метрики (время выполнения)."""
        if not self._enabled:
            return
        scenario_name = labels.get("scenario", name)
        error = labels.get("error", False)
        if scenario_name not in self._stats:
            self._stats[scenario_name] = ScenarioStats(scenario_name)
        self._stats[scenario_name].record(value, error=error)

    async def increment(self, name: str, **labels) -> None:
        """Увеличивает счётчик метрики на 1 (используется для ошибок)."""
        if not self._enabled:
            return
        scenario_name = labels.get("scenario", name)
        if scenario_name not in self._stats:
            self._stats[scenario_name] = ScenarioStats(scenario_name)
        if labels.get("error", False):
            self._stats[scenario_name].errors += 1

    def get_stats(self) -> List[ScenarioStats]:
        """Возвращает список статистики всех сценариев."""
        return list(self._stats.values())

    def clear(self) -> None:
        """Очищает все метрики."""
        self._stats.clear()


_metrics_instance: Optional[InMemoryMetrics] = None


def get_metrics() -> InMemoryMetrics:
    """Возвращает глобальный экземпляр InMemoryMetrics."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = InMemoryMetrics()
    return _metrics_instance