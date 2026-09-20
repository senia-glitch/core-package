"""Тесты run(): валидация DTO и гарантия Response-модели."""

import pytest
from pydantic import BaseModel

from core import BaseScenario, ScenarioRegistry, register_scenario
from core.startup import run, _require_state
from core.interfaces import IDatabase
from core import start_core, reset_core


class DummyDB(IDatabase):
    async def create(self, entity, data): return {}
    async def read(self, entity, id): return None
    async def update(self, entity, id, data): return {}
    async def delete(self, entity, id): return True
    async def query(self, description, params): return []


class MyDTO(BaseModel):
    name: str
    age: int


class MyResponse(BaseModel):
    greeting: str


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    reset_core()


# ---------------------------------------------------------------------------
# Валидация DTO
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_validates_dto_type():
    @register_scenario("_test_dto_validate", dto=MyDTO)
    class ValidateScenario(BaseScenario):
        async def execute(self, dto):
            return {"greeting": f"Hello, {dto.name}!"}

    await start_core(db=DummyDB())

    with pytest.raises(ValueError, match="ожидался DTO MyDTO, получен dict"):
        await run("_test_dto_validate", {"name": "Alice"})


@pytest.mark.asyncio
async def test_run_accepts_correct_dto():
    @register_scenario("_test_dto_correct", dto=MyDTO)
    class CorrectScenario(BaseScenario):
        async def execute(self, dto):
            return {"greeting": f"Hello, {dto.name}!"}

    await start_core(db=DummyDB())

    result = await run("_test_dto_correct", MyDTO(name="Alice", age=30))
    assert result == {"greeting": "Hello, Alice!"}


@pytest.mark.asyncio
async def test_run_without_dto_validation():
    """Сценарий без dto-метаданные принимает любой объект."""
    @register_scenario("_test_no_dto_val")
    class AnyScenario(BaseScenario):
        async def execute(self, dto):
            return {"received": str(dto)}

    await start_core(db=DummyDB())

    result = await run("_test_no_dto_val", "just a string")
    assert result == {"received": "just a string"}


# ---------------------------------------------------------------------------
# Response-модель
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_returns_response_instance():
    @register_scenario("_test_resp_model", response=MyResponse)
    class RespScenario(BaseScenario):
        async def execute(self, dto):
            return MyResponse(greeting="Hello!")

    await start_core(db=DummyDB())

    result = await run("_test_resp_model", {})
    assert isinstance(result, MyResponse)
    assert result.greeting == "Hello!"


@pytest.mark.asyncio
async def test_run_converts_dict_to_response():
    """Если execute вернул dict — run() создаёт Response-модель из него."""
    @register_scenario("_test_dict_to_resp", response=MyResponse)
    class DictScenario(BaseScenario):
        async def execute(self, dto):
            return {"greeting": "Hello from dict!"}

    await start_core(db=DummyDB())

    result = await run("_test_dict_to_resp", {})
    assert isinstance(result, MyResponse)
    assert result.greeting == "Hello from dict!"


@pytest.mark.asyncio
async def test_run_converts_pydantic_model_to_response():
    """Если execute вернул другую Pydantic-модель — run() конвертирует."""
    class OtherModel(BaseModel):
        greeting: str
        extra: str = "extra"

    @register_scenario("_test_pydantic_convert", response=MyResponse)
    class ConvertScenario(BaseScenario):
        async def execute(self, dto):
            return OtherModel(greeting="Converted!", extra="ignored")

    await start_core(db=DummyDB())

    result = await run("_test_pydantic_convert", {})
    assert isinstance(result, MyResponse)
    assert result.greeting == "Converted!"


@pytest.mark.asyncio
async def test_run_without_response_returns_raw():
    """Без response-модели результат возвращается как есть."""
    @register_scenario("_test_raw_resp")
    class RawScenario(BaseScenario):
        async def execute(self, dto):
            return {"raw": True}

    await start_core(db=DummyDB())

    result = await run("_test_raw_resp", {})
    assert result == {"raw": True}


# ---------------------------------------------------------------------------
# Комбинация DTO + Response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_with_both_dto_and_response():
    @register_scenario("_test_both", response=MyResponse, dto=MyDTO)
    class BothScenario(BaseScenario):
        async def execute(self, dto):
            return {"greeting": f"Hello, {dto.name}!"}

    await start_core(db=DummyDB())

    result = await run("_test_both", MyDTO(name="Bob", age=25))
    assert isinstance(result, MyResponse)
    assert result.greeting == "Hello, Bob!"


@pytest.mark.asyncio
async def test_run_both_wrong_dto_fails_before_execute():
    """Неверный DTO отлавливается до вызова execute."""
    @register_scenario("_test_both_fail", response=MyResponse, dto=MyDTO)
    class BothFailScenario(BaseScenario):
        async def execute(self, dto):
            # Этот код не должен выполниться
            raise RuntimeError("should not reach here")

    await start_core(db=DummyDB())

    with pytest.raises(ValueError, match="ожидался DTO MyDTO"):
        await run("_test_both_fail", "wrong dto")
