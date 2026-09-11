# tests/test_metrics.py
"""Тесты встроенных метрик."""

import pytest
from core import InMemoryMetrics, get_metrics


@pytest.mark.asyncio
async def test_metrics_record():
    metrics = InMemoryMetrics()
    await metrics.record("test_scenario", 150.5, scenario="test_scenario")
    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].name == "test_scenario"
    assert stats[0].calls == 1
    assert stats[0].errors == 0
    assert stats[0].total_time_ms == 150.5
    assert stats[0].avg_time_ms == 150.5


@pytest.mark.asyncio
async def test_metrics_record_with_error():
    """Проверяем, что при записи с error=True увеличивается счётчик ошибок."""
    metrics = InMemoryMetrics()
    await metrics.record("test_scenario", 100.0, scenario="test_scenario", error=True)
    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].calls == 1
    assert stats[0].errors == 1


@pytest.mark.asyncio
async def test_metrics_increment_error():
    metrics = InMemoryMetrics()
    await metrics.increment("test_scenario", scenario="test_scenario", error=True)
    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].calls == 0  # increment не увеличивает calls
    assert stats[0].errors == 1


@pytest.mark.asyncio
async def test_metrics_increment_without_error():
    """Проверяем, что increment без метки error не увеличивает счётчик ошибок."""
    metrics = InMemoryMetrics()
    await metrics.increment("test_scenario", scenario="test_scenario")
    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].calls == 0
    assert stats[0].errors == 0


@pytest.mark.asyncio
async def test_metrics_clear():
    metrics = InMemoryMetrics()
    await metrics.record("test", 1.0)
    assert len(metrics.get_stats()) == 1
    metrics.clear()
    assert len(metrics.get_stats()) == 0


@pytest.mark.asyncio
async def test_get_metrics_singleton():
    m1 = get_metrics()
    m2 = get_metrics()
    assert m1 is m2


@pytest.mark.asyncio
async def test_metrics_disabled(monkeypatch):
    """При выключенных метриках record и increment не должны ничего записывать."""
    monkeypatch.setenv("CORE_METRICS_ENABLED", "false")
    metrics = InMemoryMetrics()  # _enabled будет False
    await metrics.record("test_scenario", 100.0, scenario="test_scenario")
    await metrics.increment("test_scenario", scenario="test_scenario", error=True)
    assert len(metrics.get_stats()) == 0
    monkeypatch.undo()


@pytest.mark.asyncio
async def test_metrics_avg_zero_when_no_calls():
    """Если сценарий ещё не вызывался, avg_time_ms = 0.0, а не ошибка."""
    metrics = InMemoryMetrics()
    await metrics.increment("only_errors", scenario="only_errors", error=True)
    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].calls == 0
    assert stats[0].avg_time_ms == 0.0