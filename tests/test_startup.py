# tests/test_startup.py
"""Тесты точки входа ядра."""

import pytest

from core import (
    BaseScenario,
    IDatabase,
    ScenarioRegistry,
    start_core,
    run,
    get_db,
    get_cache,
    get_logger,
    get_core_metrics,
    reset_core,
    register_scenario,
)


class DummyDB(IDatabase):
    async def create(self, entity, data): return {}
    async def read(self, entity, id): return None
    async def update(self, entity, id, data): return {}
    async def delete(self, entity, id): return True
    async def custom(self, sql, params): return []


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    reset_core()


def test_get_db_before_start_raises():
    with pytest.raises(RuntimeError, match="Ядро не запущено"):
        get_db()


@pytest.mark.asyncio
async def test_start_core_with_db():
    db = DummyDB()
    await start_core(db=db)

    assert get_db() is db
    assert get_cache() is not None
    assert get_logger() is not None
    assert get_core_metrics() is not None


@pytest.mark.asyncio
async def test_start_core_rejects_double_call():
    await start_core(db=DummyDB())
    with pytest.raises(RuntimeError, match="уже запущено"):
        await start_core(db=DummyDB())


@pytest.mark.asyncio
async def test_start_core_rejects_both_db_and_router():
    with pytest.raises(ValueError, match="только один"):
        await start_core(db=DummyDB(), router=object())


@pytest.mark.asyncio
async def test_start_core_rejects_nothing():
    with pytest.raises(ValueError, match="router.*или db"):
        await start_core()


@pytest.mark.asyncio
async def test_run_scenario_end_to_end():
    @register_scenario("_test_hello")
    class Hello(BaseScenario):
        async def execute(self, dto):
            return {"greeting": f"Hello, {dto}!"}

    await start_core(db=DummyDB())

    result = await run("_test_hello", "Alice")
    assert result == {"greeting": "Hello, Alice!"}


@pytest.mark.asyncio
async def test_reset_allows_restart():
    await start_core(db=DummyDB())
    reset_core()
    # После сброса ядро снова доступно
    await start_core(db=DummyDB())
    assert get_db() is not None


@pytest.mark.asyncio
async def test_start_core_with_router_uses_adapter():
    """Передача router оборачивает его в EventInfraDatabaseAdapter."""
    fake_router = object()
    await start_core(router=fake_router)

    db = get_db()
    # Проверяем, что это адаптер, а внутри — наш fake_router
    from core.adapters.event_infra import EventInfraDatabaseAdapter
    assert isinstance(db, EventInfraDatabaseAdapter)
    assert db._router is fake_router


@pytest.mark.asyncio
async def test_start_core_with_discover(tmp_path, monkeypatch):
    """start_core(discover=...) должен импортировать пакет со сценариями."""
    # Создаём пакет со сценарием
    pkg = tmp_path / "sample_discover"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "hello.py").write_text(
        "from core import BaseScenario, register_scenario\n"
        "@register_scenario('discovered_hello')\n"
        "class Hello(BaseScenario):\n"
        "    async def execute(self, dto): return {'ok': True}\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    await start_core(db=DummyDB(), discover="sample_discover")

    # Сценарий зарегистрирован
    assert "discovered_hello" in ScenarioRegistry.list_scenarios()


@pytest.mark.asyncio
async def test_start_core_router_but_adapter_unavailable(monkeypatch):
    """Если адаптер недоступен (event-infra не установлен) — понятный ImportError.

    Трюк: sys.modules["<module>"] = None заставляет Python бросить ImportError
    при попытке импорта, как если бы модуля не существовало.
    """
    import sys

    # Убираем уже загруженный модуль и ставим «заглушку» — None
    monkeypatch.setitem(sys.modules, "core.adapters.event_infra", None)

    with pytest.raises(ImportError, match="Для передачи router установите event-infra"):
        await start_core(router=object())