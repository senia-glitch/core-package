# tests/test_logger.py
"""Тесты встроенного логгера."""
import os
import pytest
from core import ConsoleLogger


@pytest.mark.asyncio
async def test_console_logger_creation():
    logger = ConsoleLogger("test_logger_creation")
    # Уровень по умолчанию не установлен (0 = NOTSET), обработчик добавлен
    assert logger._logger.name == "test_logger_creation"
    assert logger._logger.level == 0
    assert len(logger._logger.handlers) == 1


@pytest.mark.asyncio
async def test_console_logger_methods_set_level():
    logger = ConsoleLogger("test_logger_methods")
    await logger.info("Info message")
    # После вызова уровень должен стать INFO (20)
    assert logger._logger.level == 20
    await logger.debug("Debug message")
    await logger.warning("Warning message")
    await logger.error("Error message")
    await logger.critical("Critical message")
    # Ничего не падает
    assert True


@pytest.mark.asyncio
async def test_logger_custom_level_dynamic(monkeypatch):
    # Устанавливаем DEBUG
    monkeypatch.setenv("CORE_LOG_LEVEL", "DEBUG")
    logger = ConsoleLogger("test_custom_dynamic")
    await logger.debug("Debug message")
    assert logger._logger.level == 10
    # Меняем на WARNING
    monkeypatch.setenv("CORE_LOG_LEVEL", "WARNING")
    await logger.warning("Warning message")
    assert logger._logger.level == 30
    monkeypatch.undo()


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