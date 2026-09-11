"""Тесты реестра сценариев."""

import logging
from pathlib import Path

import pytest

from core import BaseScenario, ScenarioRegistry, register_scenario


class DummyScenario(BaseScenario):
    async def execute(self, dto):
        return {"ok": True}


@pytest.fixture(autouse=True)
def reset_registry():
    """Перед каждым тестом очищаем реестр."""
    ScenarioRegistry._scenarios.clear()
    yield
    ScenarioRegistry._scenarios.clear()


# ---------------------------------------------------------------------------
# register / get / list
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# @register_scenario
# ---------------------------------------------------------------------------


def test_register_scenario_decorator():
    @register_scenario("decorated")
    class Decorated(DummyScenario):
        pass

    assert "decorated" in ScenarioRegistry.list_scenarios()
    assert ScenarioRegistry.list_scenarios()["decorated"] is Decorated


def test_register_scenario_duplicate():
    @register_scenario("dup")
    class First(DummyScenario):
        pass

    with pytest.raises(ValueError, match="already registered"):
        @register_scenario("dup")
        class Second(DummyScenario):
            pass


def test_register_scenario_returns_class():
    """Декоратор должен вернуть тот же класс, что получил."""
    class Original(DummyScenario):
        pass

    returned = register_scenario("orig")(Original)
    assert returned is Original


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------


def _make_pkg(tmp_path: Path, name: str) -> Path:
    """Создаёт временный пакет с __init__.py и возвращает путь к нему."""
    pkg = tmp_path / name
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    return pkg


def test_discover_missing_package():
    """Несуществующий пакет не падает, возвращает пустой список."""
    loaded = ScenarioRegistry.discover("definitely.not.a.real.package.xyz")
    assert loaded == []


def test_discover_not_a_package(tmp_path, monkeypatch):
    """Модуль без __path__ (не пакет) — warning, пустой список."""
    # sys.path временно добавим, чтобы importlib нашёл модуль
    (tmp_path / "solo_module.py").write_text("X = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    loaded = ScenarioRegistry.discover("solo_module")
    assert loaded == []


def test_discover_loads_modules(tmp_path, monkeypatch, caplog):
    """Пакет с несколькими модулями: все импортируются, декораторы срабатывают."""
    pkg = _make_pkg(tmp_path, "sample_scenarios")
    (pkg / "hello.py").write_text(
        "from core import BaseScenario, register_scenario\n"
        "class DummyDB: pass\n"
        "@register_scenario('hello')\n"
        "class Hello(BaseScenario):\n"
        "    async def execute(self, dto): return {'ok': True}\n",
        encoding="utf-8",
    )
    (pkg / "bye.py").write_text(
        "from core import BaseScenario, register_scenario\n"
        "@register_scenario('bye')\n"
        "class Bye(BaseScenario):\n"
        "    async def execute(self, dto): return {'ok': True}\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    loaded = ScenarioRegistry.discover("sample_scenarios")

    assert "sample_scenarios.hello" in loaded
    assert "sample_scenarios.bye" in loaded
    assert "hello" in ScenarioRegistry.list_scenarios()
    assert "bye" in ScenarioRegistry.list_scenarios()


def test_discover_skips_underscore_files(tmp_path, monkeypatch):
    """Файлы, начинающиеся с _, не импортируются."""
    pkg = _make_pkg(tmp_path, "with_private")
    (pkg / "_private.py").write_text("raise RuntimeError('must not load')\n", encoding="utf-8")
    (pkg / "public.py").write_text(
        "from core import BaseScenario, register_scenario\n"
        "@register_scenario('pub')\n"
        "class Pub(BaseScenario):\n"
        "    async def execute(self, dto): return {'ok': True}\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    loaded = ScenarioRegistry.discover("with_private")

    assert "with_private.public" in loaded
    assert "with_private._private" not in loaded
    assert "pub" in ScenarioRegistry.list_scenarios()


def test_discover_warns_on_bad_module(tmp_path, monkeypatch, caplog):
    """Ошибка в одном модуле не ломает загрузку остальных."""
    pkg = _make_pkg(tmp_path, "broken_pkg")
    (pkg / "good.py").write_text(
        "from core import BaseScenario, register_scenario\n"
        "@register_scenario('good')\n"
        "class Good(BaseScenario):\n"
        "    async def execute(self, dto): return {'ok': True}\n",
        encoding="utf-8",
    )
    (pkg / "bad.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    with caplog.at_level(logging.WARNING):
        loaded = ScenarioRegistry.discover("broken_pkg")

    assert "broken_pkg.good" in loaded
    assert "broken_pkg.bad" not in loaded
    assert "good" in ScenarioRegistry.list_scenarios()
    assert any("broken_pkg.bad" in rec.message for rec in caplog.records)