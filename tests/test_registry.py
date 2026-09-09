"""Тесты реестра сценариев."""

import pytest
import logging
from core import ScenarioRegistry, BaseScenario


class DummyScenario(BaseScenario):
    async def execute(self, dto):
        return {"ok": True}


@pytest.fixture(autouse=True)
def reset_registry():
    """Перед каждым тестом очищаем реестр и сбрасываем флаг автодискаверинга."""
    ScenarioRegistry._scenarios.clear()
    ScenarioRegistry._autodiscovered = False
    yield
    ScenarioRegistry._scenarios.clear()
    ScenarioRegistry._autodiscovered = False


def test_register_and_get():
    ScenarioRegistry.register("dummy", DummyScenario)
    deps = {"db": object()}
    scenario = ScenarioRegistry.get("dummy", deps)
    assert isinstance(scenario, DummyScenario)


def test_register_duplicate():
    ScenarioRegistry.register("dummy", DummyScenario)
    with pytest.raises(ValueError, match="already registered"):
        ScenarioRegistry.register("dummy", DummyScenario)


def test_get_not_registered():
    with pytest.raises(ValueError, match="not registered"):
        ScenarioRegistry.get("unknown", {})


def test_list_scenarios():
    ScenarioRegistry.register("dummy", DummyScenario)
    scenarios = ScenarioRegistry.list_scenarios()
    assert "dummy" in scenarios
    assert scenarios["dummy"] == DummyScenario


def test_autodiscover_success(monkeypatch):
    class MockEntry:
        name = "dummy"
        def load(self):
            return DummyScenario

    class MockEntryPoints:
        def select(self, group):
            assert group == "core.scenarios"
            return [MockEntry()]

    monkeypatch.setattr("importlib.metadata.entry_points", lambda: MockEntryPoints())
    ScenarioRegistry.autodiscover()
    assert "dummy" in ScenarioRegistry.list_scenarios()


def test_autodiscover_old_python(monkeypatch):
    class MockEntry:
        name = "dummy_old"
        def load(self):
            return DummyScenario

    class MockEntryPoints(dict):
        def get(self, group, default):
            if group == "core.scenarios":
                return [MockEntry()]
            return default

    monkeypatch.setattr("importlib.metadata.entry_points", lambda: MockEntryPoints())
    ScenarioRegistry.autodiscover()
    assert "dummy_old" in ScenarioRegistry.list_scenarios()


def test_autodiscover_entry_point_error(monkeypatch, caplog):
    class BadEntry:
        name = "bad"
        def load(self):
            raise ImportError("Cannot import")

    class MockEntryPoints:
        def select(self, group):
            return [BadEntry()]

    monkeypatch.setattr("importlib.metadata.entry_points", lambda: MockEntryPoints())
    with caplog.at_level(logging.WARNING):
        ScenarioRegistry.autodiscover()
    assert "Failed to load scenario from entry point" in caplog.text
    assert "bad" not in ScenarioRegistry.list_scenarios()


def test_autodiscover_general_error(monkeypatch, caplog):
    def broken_entry_points():
        raise RuntimeError("metadata unavailable")

    monkeypatch.setattr("importlib.metadata.entry_points", broken_entry_points)
    with caplog.at_level(logging.WARNING):
        ScenarioRegistry.autodiscover()
    assert "Failed to load entry points" in caplog.text