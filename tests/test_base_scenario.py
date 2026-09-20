"""Тесты базового сценария."""

import pytest
from core import BaseScenario, IDatabase
from core.exceptions import CoreError


class DummyScenario(BaseScenario):
    async def execute(self, dto):
        return {"result": "ok"}


def test_base_scenario_instantiation():
    db = object()
    scenario = DummyScenario(db=db)
    assert scenario._db is db
    assert scenario._cache is None
    assert scenario._logger is None
    assert scenario._metrics is None


@pytest.mark.asyncio
async def test_base_scenario_execute():
    db = object()
    scenario = DummyScenario(db=db)
    result = await scenario.execute({})
    assert result == {"result": "ok"}


@pytest.mark.asyncio
async def test_base_scenario_cannot_be_instantiated():
    """BaseScenario — абстрактный, его нельзя инстанцировать напрямую."""
    db = object()
    with pytest.raises(TypeError, match="abstract"):
        BaseScenario(db=db)


def test_no_auto_metrics():
    """Проверяем, что без явного декоратора метрики не оборачиваются."""
    class MyScenario(BaseScenario):
        async def execute(self, dto):
            return "done"

    assert not hasattr(MyScenario.execute, '_core_metrics_wrapped')