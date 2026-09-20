# tests/test_logger.py
"""Тесты встроенного логгера."""
import logging
import os
import pytest
from core import ConsoleLogger


@pytest.mark.asyncio
async def test_console_logger_creation():
    logger = ConsoleLogger("test_logger_creation")
    # Уровень устанавливается в __init__ из CORE_LOG_LEVEL (по умолчанию INFO=20)
    assert logger._logger.name == "test_logger_creation"
    assert logger._logger.level == 20
    assert len(logger._logger.handlers) == 1


@pytest.mark.asyncio
async def test_console_logger_methods_set_level():
    logger = ConsoleLogger("test_console_logger_methods")
    await logger.info("Info message")
    assert logger._logger.level == 20
    await logger.debug("Debug message")
    await logger.warning("Warning message")
    await logger.error("Error message")
    await logger.critical("Critical message")
    assert logger._logger.isEnabledFor(logging.INFO)
    assert logger._logger.isEnabledFor(logging.WARNING)
    assert logger._logger.isEnabledFor(logging.ERROR)
    assert logger._logger.isEnabledFor(logging.CRITICAL)


@pytest.mark.asyncio
async def test_logger_custom_level_dynamic(monkeypatch):
    # Устанавливаем DEBUG
    monkeypatch.setenv("CORE_LOG_LEVEL", "DEBUG")
    logger = ConsoleLogger("test_custom_dynamic")
    await logger.debug("Debug message")
    assert logger._logger.level == 10
    monkeypatch.undo()


@pytest.mark.asyncio
async def test_logger_custom_level_warning(monkeypatch):
    # Устанавливаем WARNING
    monkeypatch.setenv("CORE_LOG_LEVEL", "WARNING")
    logger = ConsoleLogger("test_custom_warning")
    await logger.warning("Warning message")
    assert logger._logger.level == 30


@pytest.mark.asyncio
async def test_no_duplicate_handlers():
    logger1 = ConsoleLogger("test_no_dup")
    logger2 = ConsoleLogger("test_no_dup")
    # Оба экземпляра используют один и тот же логгер, обработчик добавляется только раз
    assert len(logger1._logger.handlers) == 1
    assert len(logger2._logger.handlers) == 1


@pytest.mark.asyncio
async def test_file_handler(monkeypatch, tmp_path):
    """Проверяем, что при указании CORE_LOG_FILE используется FileHandler."""
    log_file = tmp_path / "test.log"
    monkeypatch.setenv("CORE_LOG_FILE", str(log_file))
    logger = ConsoleLogger("file_logger")
    await logger.info("File message")

    # Проверяем, что файл создан и содержит сообщение
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "File message" in content

    # Проверяем, что обработчик действительно FileHandler
    handler = logger._logger.handlers[0]
    assert isinstance(handler, __import__('logging').FileHandler)

    monkeypatch.delenv("CORE_LOG_FILE", raising=False)


@pytest.mark.asyncio
async def test_logger_level_set_in_init():
    """Уровень логирования устанавливается в __init__, а не на каждый вызов."""
    import logging
    logger = ConsoleLogger("test_level_init")
    # По умолчанию CORE_LOG_LEVEL=INFO → 20
    assert logger._logger.level == logging.INFO


@pytest.mark.asyncio
async def test_logger_reserved_kwargs_filtered():
    """Зарезервированные ключи logging не попадают в extra."""
    logger = ConsoleLogger("test_reserved_kwargs")
    # Не должно падать с KeyError даже если передать зарезервированный ключ
    await logger.info("test", levelname="overridden", args=("x",))
    await logger.warning("test", asctime="2026", lineno=42)
    # Проверяем что сообщения записались без ошибок
    assert logger._logger.isEnabledFor(logging.INFO)
    assert logger._logger.isEnabledFor(logging.WARNING)