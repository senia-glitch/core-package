"""Тесты валидации execute через __init_subclass__."""

import pytest
from pydantic import BaseModel

from core import BaseScenario, register_scenario, ScenarioRegistry


class DummyDB:
    pass


class TestMissingExecute:
    """Класс без execute не должен создаваться."""

    def test_raises_type_error(self):
        with pytest.raises(TypeError, match="не определяет метод execute"):
            class NoExecute(BaseScenario):
                pass

    def test_abstract_subclass_skipped(self):
        """Промежуточный абстрактный класс без execute допустим."""
        class Intermediate(BaseScenario):
            __abstractmethods__ = frozenset({"execute"})

        assert issubclass(Intermediate, BaseScenario)


class TestExecuteWithoutDto:
    """execute(self) без параметра dto — ошибка."""

    def test_raises_type_error(self):
        with pytest.raises(TypeError, match="не принимает аргумент dto"):
            class NoDto(BaseScenario):
                async def execute(self):
                    return None


class TestValidExecute:
    """Корректный execute(self, dto) проходит без ошибок."""

    def test_valid_scenario(self):
        class ValidScenario(BaseScenario):
            async def execute(self, dto):
                return {"ok": True}

        assert issubclass(ValidScenario, BaseScenario)

    def test_valid_with_default_dto(self):
        class WithDefault(BaseScenario):
            async def execute(self, dto=None):
                return dto

        assert issubclass(WithDefault, BaseScenario)

    def test_valid_with_type_hint(self):
        class MyDTO(BaseModel):
            name: str

        class TypedScenario(BaseScenario):
            async def execute(self, dto: MyDTO):
                return dto.name

        assert issubclass(TypedScenario, BaseScenario)


class TestDecoratedExecute:
    """execute, обёрнутый декораторами (functools.wraps), должен работать."""

    def test_with_wraps_decorator(self):
        import functools

        def my_decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper

        class DecoratedScenario(BaseScenario):
            @my_decorator
            async def execute(self, dto):
                return {"ok": True}

        assert issubclass(DecoratedScenario, BaseScenario)

    def test_with_tracked_scenario(self):
        from core import tracked_scenario

        @tracked_scenario("tracked_test")
        class TrackedScenario(BaseScenario):
            async def execute(self, dto):
                return {"ok": True}

        assert issubclass(TrackedScenario, BaseScenario)


class TestRegisterScenarioWithInitSubclass:
    """Проверяем, что @register_scenario работает с __init_subclass__."""

    def test_register_with_valid_scenario(self):
        @register_scenario("_test_init_subclass_valid")
        class Valid(BaseScenario):
            async def execute(self, dto):
                return {"ok": True}

        assert "_test_init_subclass_valid" in ScenarioRegistry.list_scenarios()

    def test_cleanup(self):
        ScenarioRegistry._scenarios.clear()
