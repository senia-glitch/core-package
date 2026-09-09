# tests/test_config.py
"""Тесты конфигурации и переменных окружения."""

import os
import pytest
from core import config
from pathlib import Path
import importlib


def test_get_env_var_default():
    assert config.get_env_var("NON_EXISTENT_VAR") == ""
    assert config.get_env_var("NON_EXISTENT_VAR", "default") == "default"


def test_get_env_var_with_env(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "hello")
    assert config.get_env_var("TEST_VAR") == "hello"


def test_get_env_bool_default():
    assert config.get_env_bool("NON_EXISTENT_BOOL") is False
    assert config.get_env_bool("NON_EXISTENT_BOOL", default=True) is True


def test_get_env_bool_values(monkeypatch):
    monkeypatch.setenv("BOOL_TRUE", "true")
    assert config.get_env_bool("BOOL_TRUE") is True
    monkeypatch.setenv("BOOL_TRUE", "1")
    assert config.get_env_bool("BOOL_TRUE") is True
    monkeypatch.setenv("BOOL_TRUE", "yes")
    assert config.get_env_bool("BOOL_TRUE") is True
    monkeypatch.setenv("BOOL_TRUE", "on")
    assert config.get_env_bool("BOOL_TRUE") is True

    monkeypatch.setenv("BOOL_FALSE", "false")
    assert config.get_env_bool("BOOL_FALSE") is False
    monkeypatch.setenv("BOOL_FALSE", "0")
    assert config.get_env_bool("BOOL_FALSE") is False
    monkeypatch.setenv("BOOL_FALSE", "no")
    assert config.get_env_bool("BOOL_FALSE") is False
    monkeypatch.setenv("BOOL_FALSE", "off")
    assert config.get_env_bool("BOOL_FALSE") is False


def test_get_env_int_default():
    assert config.get_env_int("NON_EXISTENT_INT") == 0
    assert config.get_env_int("NON_EXISTENT_INT", 42) == 42


def test_get_env_int_with_env(monkeypatch):
    monkeypatch.setenv("INT_VAR", "123")
    assert config.get_env_int("INT_VAR") == 123
    monkeypatch.setenv("INT_VAR", "abc")
    assert config.get_env_int("INT_VAR", 999) == 999


def test_get_env_float_default():
    assert config.get_env_float("NON_EXISTENT_FLOAT") == 0.0
    assert config.get_env_float("NON_EXISTENT_FLOAT", 3.14) == 3.14


def test_get_env_float_with_env(monkeypatch):
    monkeypatch.setenv("FLOAT_VAR", "3.14")
    assert config.get_env_float("FLOAT_VAR") == 3.14
    monkeypatch.setenv("FLOAT_VAR", "abc")
    assert config.get_env_float("FLOAT_VAR", 2.71) == 2.71


def test_load_dotenv_from_cwd(monkeypatch, tmp_path):
    """Файл .core-package.env в текущей директории загружается."""
    env_file = tmp_path / ".core-package.env"
    env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another")
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    assert config.get_env_var("TEST_KEY") == "test_value"
    monkeypatch.undo()
    importlib.reload(config)


def test_load_dotenv_from_parent(monkeypatch, tmp_path):
    """Файл .core-package.env в родительской директории находится."""
    parent = tmp_path / "parent"
    parent.mkdir()
    env_file = parent / ".core-package.env"
    env_file.write_text("PARENT_KEY=parent_value")
    child = parent / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    importlib.reload(config)
    assert config.get_env_var("PARENT_KEY") == "parent_value"
    monkeypatch.undo()
    importlib.reload(config)


def test_load_dotenv_explicit_path(monkeypatch, tmp_path):
    """Явный путь через CORE_ENV_PATH имеет приоритет."""
    env_file = tmp_path / "custom.env"
    env_file.write_text("EXPLICIT_KEY=explicit_value")
    monkeypatch.setenv("CORE_ENV_PATH", str(env_file))
    monkeypatch.chdir(tmp_path)  # на всякий случай
    importlib.reload(config)
    assert config.get_env_var("EXPLICIT_KEY") == "explicit_value"
    monkeypatch.undo()
    importlib.reload(config)


def test_load_dotenv_explicit_path_nonexistent(monkeypatch, tmp_path):
    """Если CORE_ENV_PATH указывает на несуществующий файл, загрузки не происходит."""
    monkeypatch.setenv("CORE_ENV_PATH", str(tmp_path / "nonexistent.env"))
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    # Переменная из несуществующего файла не должна быть установлена
    assert config.get_env_var("SHOULD_NOT_EXIST") == ""
    monkeypatch.undo()
    importlib.reload(config)


def test_no_env_file(monkeypatch, tmp_path):
    """Если файла нет, переменные окружения не загружаются."""
    monkeypatch.delenv("CORE_ENV_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    # Не должно быть переменной из несуществующего файла
    assert config.get_env_var("NON_EXISTENT_FROM_FILE") == ""
    monkeypatch.undo()
    importlib.reload(config)