# tests/test_metrics.py
"""Тесты встроенных метрик."""

import asyncio
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


@pytest.mark.asyncio
async def test_metrics_min_time_ms_safe():
    """min_time_ms_safe возвращает 0.0 при отсутствии вызовов и реальное минимум иначе."""
    metrics = InMemoryMetrics()
    await metrics.record("s", 100.0, scenario="s")
    await metrics.record("s", 50.0, scenario="s")
    stats = metrics.get_stats()
    assert stats[0].min_time_ms_safe == 50.0


@pytest.mark.asyncio
async def test_metrics_max_time_ms_safe():
    """max_time_ms_safe возвращает 0.0 при отсутствии вызовов и реальное максимум иначе."""
    metrics = InMemoryMetrics()
    await metrics.record("s", 100.0, scenario="s")
    await metrics.record("s", 200.0, scenario="s")
    stats = metrics.get_stats()
    assert stats[0].max_time_ms_safe == 200.0


@pytest.mark.asyncio
async def test_metrics_min_max_safe_zero_when_no_calls():
    """Если сценарий не вызывался (только increment), min/max = 0.0."""
    metrics = InMemoryMetrics()
    await metrics.increment("s", scenario="s", error=True)
    stats = metrics.get_stats()
    assert stats[0].min_time_ms_safe == 0.0
    assert stats[0].max_time_ms_safe == 0.0


@pytest.mark.asyncio
async def test_metrics_concurrent_access():
    """Проверяем потокобезопасность: 50 параллельных record() без ошибок."""
    metrics = InMemoryMetrics()

    async def worker(i):
        await metrics.record(f"s{i % 5}", 10.0, scenario=f"s{i % 5}")

    await asyncio.gather(*(worker(i) for i in range(50)))

    stats = metrics.get_stats()
    total_calls = sum(s.calls for s in stats)
    assert total_calls == 50