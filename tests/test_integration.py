# tests/test_integration.py
"""Интеграционные тесты для проверки работоспособности примера."""

import os
import subprocess
import sys
from pathlib import Path


def test_run_example_works(tmp_path, monkeypatch):
    """Проверяет, что пример main_example.py выполняется без ошибок."""
    monkeypatch.chdir(tmp_path)

    from core.cli import init
    original_argv = sys.argv
    sys.argv = ["core-init", "--force"]
    try:
        init()
    finally:
        sys.argv = original_argv

    # Файл называется main_example.py
    example = tmp_path / "core_project" / "examples" / "main_example.py"
    assert example.exists()

    result = subprocess.run(
        [sys.executable, str(example)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "ЗАПУСК ПРИМЕРА core-package" in result.stdout
    assert "Ответ: Hello, Alice!" in result.stdout
    assert "Ответ: Hello, Bob!" in result.stdout
    assert "МЕТРИКИ ВЫПОЛНЕНИЯ" in result.stdout
    # Метрика greeting_calls появляется, так как increment вызывается
    assert "greeting_calls" in result.stdout