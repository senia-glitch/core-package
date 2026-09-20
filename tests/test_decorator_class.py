# tests/test_decorator_class.py
"""Тесты декоратора класса tracked_scenario."""

import pytest
from core import BaseScenario, tracked_scenario, get_metrics, InMemoryMetrics, reset_metrics
from core.interfaces import IDatabase


class DummyDB(IDatabase):
    async def create(self, entity, data): return {}
    async def read(self, entity, id): return None
    async def update(self, entity, id, data): return {}
    async def delete(self, entity, id): return True
    async def query(self, description, params): return []


@pytest.mark.asyncio
async def test_tracked_scenario_records_metrics():
    metrics = get_metrics()
    metrics.clear()

    @tracked_scenario("test_scenario")
    class MyScenario(BaseScenario):
        async def execute(self, dto):
            return {"ok": True}

    db = DummyDB()
    scenario = MyScenario(db=db)
    result = await scenario.execute({"test": 1})
    assert result == {"ok": True}

    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].name == "test_scenario"
    assert stats[0].calls == 1
    assert stats[0].errors == 0


@pytest.mark.asyncio
async def test_tracked_scenario_records_errors():
    metrics = get_metrics()
    metrics.clear()

    @tracked_scenario("failing_scenario")
    class FailingScenario(BaseScenario):
        async def execute(self, dto):
            raise ValueError("Test error")

    db = DummyDB()
    scenario = FailingScenario(db=db)
    with pytest.raises(ValueError, match="Test error"):
        await scenario.execute({})

    stats = metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].name == "failing_scenario"
    assert stats[0].calls == 1
    assert stats[0].errors == 1


@pytest.mark.asyncio
async def test_tracked_scenario_uses_passed_metrics():
    """При передаче metrics в конструктор используется именно он."""
    global_metrics = get_metrics()
    global_metrics.clear()
    local_metrics = InMemoryMetrics()

    @tracked_scenario("scenario_with_local_metrics")
    class MyScenario(BaseScenario):
        async def execute(self, dto):
            return {"ok": True}

    db = DummyDB()
    scenario = MyScenario(db=db, metrics=local_metrics)
    await scenario.execute({})

    assert len(global_metrics.get_stats()) == 0
    stats = local_metrics.get_stats()
    assert len(stats) == 1
    assert stats[0].name == "scenario_with_local_metrics"


@pytest.mark.asyncio
async def test_tracked_scenario_disabled(monkeypatch):
    monkeypatch.setenv("CORE_METRICS_ENABLED", "false")
    import importlib
    import core.metrics
    importlib.reload(core.metrics)

    metrics = get_metrics()
    metrics.clear()

    @tracked_scenario("disabled_scenario")
    class MyScenario(BaseScenario):
        async def execute(self, dto):
            return {"ok": True}

    db = DummyDB()
    scenario = MyScenario(db=db)
    result = await scenario.execute({})
    assert result == {"ok": True}
    assert len(metrics.get_stats()) == 0

    monkeypatch.undo()
    importlib.reload(core.metrics)
    reset_metrics()