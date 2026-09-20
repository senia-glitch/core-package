"""Тесты ScenarioRegistry: get_response, get_dto, get_entry и register с метаданными."""

import pytest
from pydantic import BaseModel

from core import BaseScenario, ScenarioRegistry, register_scenario


class DummyScenario(BaseScenario):
    async def execute(self, dto):
        return {"ok": True}


class SampleResponse(BaseModel):
    message: str


class SampleDTO(BaseModel):
    name: str


@pytest.fixture(autouse=True)
def reset_registry():
    ScenarioRegistry._scenarios.clear()
    yield
    ScenarioRegistry._scenarios.clear()


# ---------------------------------------------------------------------------
# register с response / dto
# ---------------------------------------------------------------------------


def test_register_with_response_and_dto():
    ScenarioRegistry.register(
        "with_meta", DummyScenario, response=SampleResponse, dto=SampleDTO,
    )
    entry = ScenarioRegistry.get_entry("with_meta")
    assert entry.scenario_cls is DummyScenario
    assert entry.response is SampleResponse
    assert entry.dto is SampleDTO


def test_register_without_metadata():
    ScenarioRegistry.register("no_meta", DummyScenario)
    entry = ScenarioRegistry.get_entry("no_meta")
    assert entry.scenario_cls is DummyScenario
    assert entry.response is None
    assert entry.dto is None


# ---------------------------------------------------------------------------
# get_response / get_dto
# ---------------------------------------------------------------------------


def test_get_response_with_metadata():
    ScenarioRegistry.register(
        "resp_test", DummyScenario, response=SampleResponse,
    )
    assert ScenarioRegistry.get_response("resp_test") is SampleResponse


def test_get_response_without_metadata():
    ScenarioRegistry.register("no_resp", DummyScenario)
    assert ScenarioRegistry.get_response("no_resp") is None


def test_get_dto_with_metadata():
    ScenarioRegistry.register(
        "dto_test", DummyScenario, dto=SampleDTO,
    )
    assert ScenarioRegistry.get_dto("dto_test") is SampleDTO


def test_get_dto_without_metadata():
    ScenarioRegistry.register("no_dto", DummyScenario)
    assert ScenarioRegistry.get_dto("no_dto") is None


def test_get_response_not_registered():
    with pytest.raises(ValueError, match="not registered"):
        ScenarioRegistry.get_response("nonexistent")


def test_get_dto_not_registered():
    with pytest.raises(ValueError, match="not registered"):
        ScenarioRegistry.get_dto("nonexistent")


def test_get_entry_not_registered():
    with pytest.raises(ValueError, match="not registered"):
        ScenarioRegistry.get_entry("nonexistent")


# ---------------------------------------------------------------------------
# list_scenarios совместимость
# ---------------------------------------------------------------------------


def test_list_scenarios_returns_classes():
    ScenarioRegistry.register("list_test", DummyScenario)
    scenarios = ScenarioRegistry.list_scenarios()
    assert scenarios["list_test"] is DummyScenario


# ---------------------------------------------------------------------------
# @register_scenario с response / dto
# ---------------------------------------------------------------------------


def test_decorator_with_metadata():
    @register_scenario("_test_dec_meta", response=SampleResponse, dto=SampleDTO)
    class MetaScenario(BaseScenario):
        async def execute(self, dto):
            return SampleResponse(message="hi")

    entry = ScenarioRegistry.get_entry("_test_dec_meta")
    assert entry.response is SampleResponse
    assert entry.dto is SampleDTO
    assert entry.scenario_cls is MetaScenario


def test_decorator_without_metadata():
    @register_scenario("_test_dec_no_meta")
    class PlainScenario(BaseScenario):
        async def execute(self, dto):
            return {"ok": True}

    entry = ScenarioRegistry.get_entry("_test_dec_no_meta")
    assert entry.response is None
    assert entry.dto is None


def test_decorator_returns_class():
    class Original(BaseScenario):
        async def execute(self, dto):
            return None

    returned = register_scenario("_test_returns")(Original)
    assert returned is Original
