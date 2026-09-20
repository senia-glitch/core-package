# tests/test_upgrade.py
"""Тесты CLI-команды core-upgrade."""

import sys
import subprocess
from unittest import mock

import pytest

from core.cli import (
    _parse_version,
    _parse_requires_python,
    _version_to_tuple,
    _parse_python_range,
    _check_python_compatibility,
    _find_pip,
    _get_local_version,
    upgrade,
)


# ============================================================
# _parse_version
# ============================================================


class TestParseVersion:
    def test_simple_version(self):
        toml = 'version = "0.3.0"'
        assert _parse_version(toml) == "0.3.0"

    def test_version_with_surrounding_context(self):
        toml = 'name = "core-package"\nversion = "1.2.3"\ndescription = "test"'
        assert _parse_version(toml) == "1.2.3"

    def test_version_not_found(self):
        toml = 'name = "core-package"\ndescription = "test"'
        assert _parse_version(toml) is None

    def test_version_in_comments_not_matched(self):
        toml = '# version = "0.1.0"\nversion = "0.2.0"'
        assert _parse_version(toml) == "0.2.0"


# ============================================================
# _parse_requires_python
# ============================================================


class TestParseRequiresPython:
    def test_simple_gte(self):
        toml = 'requires-python = ">=3.8"'
        assert _parse_requires_python(toml) == ">=3.8"

    def test_range(self):
        toml = 'requires-python = ">=3.8,<4.0"'
        assert _parse_requires_python(toml) == ">=3.8,<4.0"

    def test_not_found(self):
        toml = 'name = "core-package"'
        assert _parse_requires_python(toml) is None


# ============================================================
# _version_to_tuple
# ============================================================


class TestVersionToTuple:
    def test_three_parts(self):
        assert _version_to_tuple("0.2.0") == (0, 2, 0)

    def test_two_parts(self):
        assert _version_to_tuple("1.5") == (1, 5)

    def test_four_parts(self):
        assert _version_to_tuple("1.2.3.4") == (1, 2, 3, 4)

    def test_single_part(self):
        assert _version_to_tuple("5") == (5,)

    def test_whitespace(self):
        assert _version_to_tuple("  0.2.0  ") == (0, 2, 0)


# ============================================================
# _parse_python_range
# ============================================================


class TestParsePythonRange:
    def test_gte_only(self):
        assert _parse_python_range(">=3.8") == (3, None)

    def test_range(self):
        assert _parse_python_range(">=3.8,<4.0") == (3, 4)

    def test_narrow_range(self):
        assert _parse_python_range(">=3.9,<3.14") == (3, 3)

    def test_no_lower(self):
        assert _parse_python_range("<4.0") == (None, 4)

    def test_no_upper(self):
        assert _parse_python_range(">=3.10") == (3, None)

    def test_empty(self):
        assert _parse_python_range("") == (None, None)


# ============================================================
# _check_python_compatibility
# ============================================================


class TestCheckPythonCompatibility:
    def test_compatible_gte(self):
        assert _check_python_compatibility(">=3.8") is True

    def test_compatible_range(self):
        assert _check_python_compatibility(">=3.8,<4.0") is True

    def test_incompatible_too_old(self):
        assert _check_python_compatibility(">=4.0") is False

    def test_incompatible_too_new(self):
        assert _check_python_compatibility(">=2.0,<3.0") is False


# ============================================================
# _find_pip
# ============================================================


class TestFindPip:
    def test_returns_value(self):
        result = _find_pip()
        assert result is not None

    def test_returns_string(self):
        result = _find_pip()
        assert isinstance(result, str)


# ============================================================
# _get_local_version
# ============================================================


class TestGetLocalVersion:
    def test_returns_string(self):
        result = _get_local_version()
        assert isinstance(result, str)
        assert result  # не пустая

    def test_format(self):
        result = _get_local_version()
        parts = result.split(".")
        assert len(parts) >= 2
        for part in parts:
            assert part.isdigit()


# ============================================================
# upgrade — интеграционные тесты с мокингом
# ============================================================


class TestUpgradeFunction:
    def test_already_up_to_date(self, monkeypatch, capsys):
        """Если локальная версия >= удалённой — выводит 'Уже актуально'."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.5.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=3.8"',
        )

        upgrade()

        captured = capsys.readouterr()
        assert "Уже актуально" in captured.out

    def test_fetch_error_exits(self, monkeypatch):
        """Ошибка загрузки远程 pyproject — sys.exit(1)."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")

        def fail_fetch():
            raise ConnectionError("network error")

        monkeypatch.setattr("core.cli._fetch_remote_pyproject", fail_fetch)

        with pytest.raises(SystemExit) as exc_info:
            upgrade()
        assert exc_info.value.code == 1

    def test_invalid_remote_version_exits(self, monkeypatch):
        """Если удалённая версия не найдена — sys.exit(1)."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'name = "core-package"\nno version here',
        )

        with pytest.raises(SystemExit) as exc_info:
            upgrade()
        assert exc_info.value.code == 1

    def test_pip_not_found_exits(self, monkeypatch):
        """Если pip не найден — sys.exit(1)."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=3.8"',
        )
        monkeypatch.setattr("core.cli._find_pip", lambda: None)

        with pytest.raises(SystemExit) as exc_info:
            upgrade()
        assert exc_info.value.code == 1

    def test_incompatible_python_user_declines(self, monkeypatch, capsys):
        """При несовместимости Python и ответе 'no' — отмена."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=4.0"',
        )
        monkeypatch.setattr("core.cli._find_pip", lambda: "/usr/bin/pip")
        monkeypatch.setattr("builtins.input", lambda _: "no")

        upgrade()

        captured = capsys.readouterr()
        assert "отменено" in captured.out

    def test_incompatible_python_user_accepts(self, monkeypatch, capsys):
        """При несовместимости Python и ответе 'yes' — выполняется обновление."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=4.0"',
        )
        monkeypatch.setattr("core.cli._find_pip", lambda: "/usr/bin/pip")
        monkeypatch.setattr("builtins.input", lambda _: "yes")
        mock_run = mock.MagicMock(return_value=mock.MagicMock(returncode=0))
        monkeypatch.setattr("core.cli.subprocess.run", mock_run)

        upgrade()

        captured = capsys.readouterr()
        assert "0.2.0" in captured.out
        assert "0.3.0" in captured.out
        mock_run.assert_called_once()

    def test_successful_upgrade(self, monkeypatch, capsys):
        """Успешное обновление — pip install --upgrade вызван."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=3.8"',
        )
        monkeypatch.setattr("core.cli._find_pip", lambda: "/usr/bin/pip")
        mock_run = mock.MagicMock(return_value=mock.MagicMock(returncode=0))
        monkeypatch.setattr("core.cli.subprocess.run", mock_run)

        upgrade()

        captured = capsys.readouterr()
        assert "0.2.0" in captured.out
        assert "0.3.0" in captured.out
        assert "Обновление завершено" in captured.out

        called_args = mock_run.call_args[0][0]
        assert "pip" in called_args[-1] or "install" in called_args
        assert "--upgrade" in called_args
        assert "git+https://github.com/senia-glitch/core-package.git" in called_args

    def test_upgrade_via_python_m_pip(self, monkeypatch):
        """Если pip из PATH не найден — используется sys.executable -m pip."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=3.8"',
        )
        monkeypatch.setattr("core.cli._find_pip", lambda: sys.executable)
        mock_run = mock.MagicMock(return_value=mock.MagicMock(returncode=0))
        monkeypatch.setattr("core.cli.subprocess.run", mock_run)

        upgrade()

        called_args = mock_run.call_args[0][0]
        assert called_args[0] == sys.executable
        assert called_args[1] == "-m"
        assert called_args[2] == "pip"

    def test_upgrade_fails_exits(self, monkeypatch):
        """Ошибка pip — sys.exit(1)."""
        monkeypatch.setattr("core.cli._get_local_version", lambda: "0.2.0")
        monkeypatch.setattr(
            "core.cli._fetch_remote_pyproject",
            lambda: 'version = "0.3.0"\nrequires-python = ">=3.8"',
        )
        monkeypatch.setattr("core.cli._find_pip", lambda: "/usr/bin/pip")
        mock_run = mock.MagicMock(return_value=mock.MagicMock(returncode=1))
        monkeypatch.setattr("core.cli.subprocess.run", mock_run)

        with pytest.raises(SystemExit) as exc_info:
            upgrade()
        assert exc_info.value.code == 1


# ============================================================
# edge cases
# ============================================================


class TestUpgradeEdgeCases:
    def test_local_version_tuple_comparison(self):
        """Попарное сравнение кортежей работает корректно."""
        assert (0, 2, 0) < (0, 3, 0)
        assert (0, 2, 0) < (1, 0, 0)
        assert (0, 2, 0) == (0, 2, 0)
        assert (0, 2, 1) > (0, 2, 0)
        assert (0, 2, 0) >= (0, 2, 0)
        assert not (0, 2, 0) >= (0, 3, 0)

    def test_parse_version_real_toml(self):
        """Парсинг реального содержимого pyproject.toml."""
        toml = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "core-package"
version = "0.2.0"
description = "Платформа для построения бизнес-сценариев с абстракциями и утилитами"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
"""
        assert _parse_version(toml) == "0.2.0"
        assert _parse_requires_python(toml) == ">=3.8"

    def test_find_pip_returns_actual_path(self):
        """_find_pip возвращает реальный путь к pip."""
        result = _find_pip()
        # pip установлен в тестовом окружении
        assert result is not None
