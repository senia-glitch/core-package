# src/core/metrics.py
"""Встроенная реализация IMetrics для хранения метрик в памяти."""

import asyncio
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

    @classmethod
    def _from_values(cls, name, calls, errors, total_time_ms, min_time_ms, max_time_ms):
        obj = cls(name)
        obj.calls = calls
        obj.errors = errors
        obj.total_time_ms = total_time_ms
        obj.min_time_ms = min_time_ms
        obj.max_time_ms = max_time_ms
        return obj

    @property
    def avg_time_ms(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.total_time_ms / self.calls

    @property
    def min_time_ms_safe(self) -> float:
        """Минимальное время (0.0 если вызовов не было)."""
        if self.calls == 0:
            return 0.0
        return self.min_time_ms

    @property
    def max_time_ms_safe(self) -> float:
        """Максимальное время (0.0 если вызовов не было)."""
        if self.calls == 0:
            return 0.0
        return self.max_time_ms


class InMemoryMetrics(IMetrics):
    """Реализация IMetrics с хранением метрик в памяти."""

    def __init__(self):
        self._stats: Dict[str, ScenarioStats] = {}
        self._enabled = get_env_bool("CORE_METRICS_ENABLED", True)
        self._lock = asyncio.Lock()

    async def record(self, name: str, value: float, **labels) -> None:
        """Записывает числовое значение метрики (время выполнения)."""
        if not self._enabled:
            return
        async with self._lock:
            scenario_name = labels.get("scenario", name)
            error = labels.get("error", False)
            if scenario_name not in self._stats:
                self._stats[scenario_name] = ScenarioStats(scenario_name)
            self._stats[scenario_name].record(value, error=error)

    async def increment(self, name: str, **labels) -> None:
        """Увеличивает счётчик метрики на 1 (используется для ошибок)."""
        if not self._enabled:
            return
        async with self._lock:
            scenario_name = labels.get("scenario", name)
            if scenario_name not in self._stats:
                self._stats[scenario_name] = ScenarioStats(scenario_name)
            if labels.get("error", False):
                self._stats[scenario_name].errors += 1

    def get_stats(self) -> List[ScenarioStats]:
        """Возвращает копии статистики всех сценариев."""
        return [
            ScenarioStats._from_values(
                s.name, s.calls, s.errors, s.total_time_ms, s.min_time_ms, s.max_time_ms
            )
            for s in self._stats.values()
        ]

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


def reset_metrics() -> None:
    """Сбрасывает глобальный экземпляр метрик."""
    global _metrics_instance
    if _metrics_instance is not None:
        _metrics_instance.clear()
    _metrics_instance = None