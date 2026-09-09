# tests/test_decorator.py
"""Тесты декоратора метрик."""
import os
import pytest
from core import track_metrics, get_metrics, InMemoryMetrics


@pytest.mark.asyncio
async def test_track_metrics_success():
    metrics = get_metrics()
    metrics.clear()

    @track_metrics("test_decorator")
    async def dummy_func():
        return "ok"

    result = await dummy_func()
    assert result == "ok"

    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].name == "test_decorator"
    assert stats[0].calls == 1
    assert stats[0].errors == 0
    assert stats[0].total_time_ms > 0


@pytest.mark.asyncio
async def test_track_metrics_error():
    metrics = get_metrics()
    metrics.clear()

    @track_metrics("test_decorator")
    async def failing_func():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        await failing_func()

    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].calls == 1
    assert stats[0].errors == 1


@pytest.mark.asyncio
async def test_track_metrics_uses_passed_metrics():
    """Проверяем, что декоратор использует self._metrics, а не глобальный."""
    global_metrics = get_metrics()
    global_metrics.clear()
    local_metrics = InMemoryMetrics()

    class Dummy:
        def __init__(self):
            self._metrics = local_metrics

        @track_metrics("local_metric")
        async def method(self):
            return "done"

    dummy = Dummy()
    await dummy.method()

    # Глобальные метрики не должны измениться
    assert len(global_metrics.get_stats()) == 0
    # Локальные должны содержать запись
    stats = local_metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].name == "local_metric"
    assert stats[0].calls == 1


@pytest.mark.asyncio
async def test_track_metrics_disabled(monkeypatch):
    monkeypatch.setenv("CORE_METRICS_ENABLED", "false")
    import importlib
    import core.metrics
    importlib.reload(core.metrics)

    metrics = get_metrics()
    metrics.clear()

    @track_metrics("test_disabled")
    async def dummy_func():
        return "ok"

    result = await dummy_func()
    assert result == "ok"
    assert len(metrics.get_stats()) == 0

    monkeypatch.undo()
    importlib.reload(core.metrics)