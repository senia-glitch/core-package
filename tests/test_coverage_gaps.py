"""Тесты для непокрытых строк: кеш, startup, security, edge cases."""

import pytest
from pydantic import BaseModel

from core import BaseScenario, ScenarioRegistry, register_scenario
from core.cache import TTLCache
from core.startup import run, get_scenario, _require_state, start_core, reset_core
from core.interfaces import IDatabase
from core.utils.security import extract_token_info, create_access_token


class DummyDB(IDatabase):
    async def create(self, entity, data): return {}
    async def read(self, entity, id): return None
    async def update(self, entity, id, data): return {}
    async def delete(self, entity, id): return True
    async def query(self, description, params): return []


class SampleDTO(BaseModel):
    name: str


class SampleResponse(BaseModel):
    greeting: str


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    reset_core()


# ---------------------------------------------------------------------------
# cache.py:20,22 — ValueError validation
# ---------------------------------------------------------------------------


def test_cache_max_size_zero():
    with pytest.raises(ValueError, match="max_size must be >= 1"):
        TTLCache(max_size=0)


def test_cache_ttl_seconds_zero():
    with pytest.raises(ValueError, match="ttl_seconds must be >= 1"):
        TTLCache(ttl_seconds=0)


def test_cache_negative_max_size():
    with pytest.raises(ValueError, match="max_size must be >= 1"):
        TTLCache(max_size=-1)


def test_cache_negative_ttl():
    with pytest.raises(ValueError, match="ttl_seconds must be >= 1"):
        TTLCache(ttl_seconds=-1)


# ---------------------------------------------------------------------------
# startup.py:121-122 — get_scenario
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_scenario_returns_instance():
    @register_scenario("_test_get_scenario")
    class TestScenario(BaseScenario):
        async def execute(self, dto):
            return {"ok": True}

    await start_core(db=DummyDB())
    scenario = get_scenario("_test_get_scenario")
    assert isinstance(scenario, TestScenario)
    assert scenario._db is not None
    assert scenario._cache is not None
    assert scenario._logger is not None
    assert scenario._metrics is not None


@pytest.mark.asyncio
async def test_get_scenario_not_registered():
    await start_core(db=DummyDB())
    with pytest.raises(ValueError, match="not registered"):
        get_scenario("_nonexistent_scenario_xyz")


# ---------------------------------------------------------------------------
# startup.py:166 — model_validate fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_converts_mapping_to_response():
    """Если execute вернул dict-подобный объект (не dict и не Pydantic) — model_validate."""
    @register_scenario("_test_mapping_resp", response=SampleResponse)
    class MappingScenario(BaseScenario):
        async def execute(self, dto):
            return {"greeting": "from mapping"}

    await start_core(db=DummyDB())
    result = await run("_test_mapping_resp", {})
    assert isinstance(result, SampleResponse)
    assert result.greeting == "from mapping"


@pytest.mark.asyncio
async def test_run_converts_pydantic_via_model_dump():
    """execute возвращает Pydantic модель → конвертация через model_dump()."""
    class OtherModel(BaseModel):
        greeting: str

    @register_scenario("_test_pydantic_dump", response=SampleResponse)
    class DumpScenario(BaseScenario):
        async def execute(self, dto):
            return OtherModel(greeting="dump path")

    await start_core(db=DummyDB())
    result = await run("_test_pydantic_dump", {})
    assert isinstance(result, SampleResponse)
    assert result.greeting == "dump path"


# ---------------------------------------------------------------------------
# security.py:165-166 — extract_token_info error handling
# ---------------------------------------------------------------------------


def test_extract_token_info_missing_sub():
    """payload без 'sub' → InvalidTokenError."""
    import jwt
    token = create_access_token(user_id=1, role="admin", secret="sec")
    # Создаём токен с кастомным payload без sub
    bad_payload = {"role": "admin", "type": "access", "iat": 0, "exp": 9999999999}
    bad_token = jwt.encode(bad_payload, "sec", algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError, match="Invalid token payload"):
        extract_token_info(bad_token, secret="sec")


def test_extract_token_info_non_numeric_sub():
    """payload с нечисловым 'sub' → InvalidTokenError."""
    import jwt
    bad_payload = {"sub": "not_a_number", "role": "admin", "type": "access", "iat": 0, "exp": 9999999999}
    bad_token = jwt.encode(bad_payload, "sec", algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError, match="Invalid token payload"):
        extract_token_info(bad_token, secret="sec")


# ---------------------------------------------------------------------------
# base_scenario.py:42,45-46 — edge cases
# ---------------------------------------------------------------------------


def test_init_subclass_execute_none_in_dict():
    """execute = None в классе → validate signature не падает."""
    class NoneScenario(BaseScenario):
        execute = None

    assert issubclass(NoneScenario, BaseScenario)


def test_init_subclass_execute_with_args():
    """execute(self, *args) — VAR_POSITIONAL пропускается, dto-параметр есть."""
    class ArgsScenario(BaseScenario):
        async def execute(self, dto, *args):
            return dto

    assert issubclass(ArgsScenario, BaseScenario)


def test_init_subclass_execute_with_kwargs():
    """execute(self, dto, **kwargs) — VAR_KEYWORD пропускается."""
    class KwargsScenario(BaseScenario):
        async def execute(self, dto, **kwargs):
            return dto

    assert issubclass(KwargsScenario, BaseScenario)


# ---------------------------------------------------------------------------
# cli.py — template error handling paths
# ---------------------------------------------------------------------------


def test_cli_template_error_prints_warning(tmp_path, monkeypatch, capsys):
    """Если шаблон не найден — cli выводит предупреждение."""
    import sys
    from core.cli import init

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["core-init", "--force"])

    init()

    captured = capsys.readouterr()
    assert "Инициализация завершена" in captured.out


def test_cli_existing_pyproject_skipped(tmp_path, monkeypatch, capsys):
    """Если pyproject.toml уже существует без --force — пропускается."""
    import sys
    from core.cli import init

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["core-init"])

    # Первый запуск создаёт файлы
    init()

    # Второй запуск без --force пропускает pyproject
    init()
    captured = capsys.readouterr()
    assert "уже существует" in captured.out


def test_cli_existing_readme_skipped(tmp_path, monkeypatch, capsys):
    """Если README.md уже существует без --force — пропускается."""
    import sys
    from core.cli import init

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["core-init"])

    init()
    init()
    captured = capsys.readouterr()
    assert "уже существует" in captured.out


# ---------------------------------------------------------------------------
# startup.py:167 — model_validate fallback (dict-like, non-Pydantic)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_model_validate_fallback():
    """execute возвращает dict-субкласс (не dict напрямую) — model_validate."""
    class CustomDict(dict):
        """dict-субкласс без model_dump, isinstance(d, dict) == True."""
        pass

    @register_scenario("_test_model_validate_fallback", response=SampleResponse)
    class FallbackScenario(BaseScenario):
        async def execute(self, dto):
            return CustomDict(greeting="fallback path")

    await start_core(db=DummyDB())
    result = await run("_test_model_validate_fallback", {})
    assert isinstance(result, SampleResponse)
    assert result.greeting == "fallback path"


# ---------------------------------------------------------------------------
# base_scenario.py:47-48 — inspect.signature failure
# ---------------------------------------------------------------------------


def test_init_subclass_execute_with_inspect_error():
    """execute — дескриптор, бросающий TypeError при inspect.signature."""
    class BrokenDescriptor:
        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            raise TypeError("cannot inspect")

    class DescriptorScenario(BaseScenario):
        execute = BrokenDescriptor()

    assert issubclass(DescriptorScenario, BaseScenario)


# ---------------------------------------------------------------------------
# cli.py:87,130,132 — template error paths
# ---------------------------------------------------------------------------


def test_cli_template_error_reporting(tmp_path, monkeypatch, capsys):
    """Если шаблон не найден — cli выводит предупреждение о шаблонах."""
    import sys
    from core.cli import init, _copy_template

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["core-init", "--force"])

    original_copy = _copy_template

    def mock_copy(template_name, dest, force=False):
        if template_name == "scenario_template.py":
            return "error"
        return original_copy(template_name, dest, force)

    monkeypatch.setattr("core.cli._copy_template", mock_copy)

    init()

    captured = capsys.readouterr()
    assert "не удалось скопировать шаблоны" in captured.out


def test_cli_env_error_reporting(tmp_path, monkeypatch, capsys):
    """Если .core-package.env не удалось создать — выводится предупреждение."""
    import sys
    from core.cli import init, _copy_template

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["core-init", "--force"])

    original_copy = _copy_template

    def mock_copy(template_name, dest, force=False):
        if template_name == "env_template.txt":
            return "error"
        return original_copy(template_name, dest, force)

    monkeypatch.setattr("core.cli._copy_template", mock_copy)

    init()

    captured = capsys.readouterr()
    assert "не удалось создать .core-package.env" in captured.out
