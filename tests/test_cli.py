# tests/test_cli.py
"""Тесты CLI-команды core-init."""

import os
import tempfile
from pathlib import Path
import sys
import pytest


def test_core_init_creates_files():
    """Проверяет, что core-init создаёт ожидаемые файлы и папки."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        os.chdir(tmpdir)
        from core.cli import init

        original_argv = sys.argv
        sys.argv = ["core-init"]
        try:
            init()
        finally:
            sys.argv = original_argv

        # Корневые файлы
        assert (Path(tmpdir) / ".core-package.env").exists()
        assert (Path(tmpdir) / "pyproject.toml").exists()
        assert (Path(tmpdir) / "README.md").exists()

        # Структура core_project
        core_project = Path(tmpdir) / "core_project"
        assert core_project.exists()
        for folder in ["scenarios", "interfaces", "utils"]:
            assert (core_project / folder).exists()
            assert (core_project / folder / "__init__.py").exists()
            assert (core_project / folder / "README.md").exists()
        examples = core_project / "examples"
        assert examples.exists()
        assert (examples / "example_scenario.py").exists()
        assert (examples / "main_example.py").exists()
        assert (examples / "main_with_event_infra_example.py").exists()
        assert (examples / "README.md").exists()

def test_core_init_does_not_overwrite_without_force():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        os.chdir(tmpdir)
        from core.cli import init

        original_argv = sys.argv
        sys.argv = ["core-init"]
        try:
            init()
        finally:
            sys.argv = original_argv

        env_file = Path(tmpdir) / ".core-package.env"
        original_content = env_file.read_text(encoding="utf-8")
        env_file.write_text(original_content + "\n# custom addition\n", encoding="utf-8")

        sys.argv = ["core-init"]
        try:
            init()
        finally:
            sys.argv = original_argv

        modified = env_file.read_text(encoding="utf-8")
        assert modified.endswith("# custom addition\n")


def test_core_init_overwrites_with_force():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        os.chdir(tmpdir)
        from core.cli import init

        original_argv = sys.argv
        sys.argv = ["core-init"]
        try:
            init()
        finally:
            sys.argv = original_argv

        env_file = Path(tmpdir) / ".core-package.env"
        env_file.write_text("custom content", encoding="utf-8")

        sys.argv = ["core-init", "--force"]
        try:
            init()
        finally:
            sys.argv = original_argv

        new_content = env_file.read_text(encoding="utf-8")
        assert new_content != "custom content"
        assert "# Конфигурация core-package" in new_content


def test_copy_template_nonexistent_returns_false(tmp_path, capsys):
    """Если шаблона нет в пакете — _copy_template вернёт False."""
    from core.cli import _copy_template

    dest = tmp_path / "out.txt"
    ok = _copy_template("this_template_does_not_exist_xyz.txt", dest, force=True)
    assert ok is False
    assert not dest.exists()

    captured = capsys.readouterr()
    assert "Ошибка чтения шаблона" in captured.out