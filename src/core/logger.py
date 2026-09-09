# src/core/logger.py
"""Встроенная реализация ILogger для вывода в консоль или файл."""

import logging
from .interfaces.logger import ILogger
from .config import get_env_var


class ConsoleLogger(ILogger):
    """Реализация ILogger с использованием стандартного модуля logging."""

    def __init__(self, name: str = "core"):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            self._setup_handler()

    def _setup_handler(self):
        log_file = get_env_var("CORE_LOG_FILE", "")
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _log(self, level: int, message: str, **kwargs):
        log_level = get_env_var("CORE_LOG_LEVEL", "INFO").upper()
        self._logger.setLevel(log_level)
        self._logger.log(level, message, extra=kwargs)

    async def debug(self, message: str, **kwargs) -> None:
        self._log(logging.DEBUG, message, **kwargs)

    async def info(self, message: str, **kwargs) -> None:
        self._log(logging.INFO, message, **kwargs)

    async def warning(self, message: str, **kwargs) -> None:
        self._log(logging.WARNING, message, **kwargs)

    async def error(self, message: str, **kwargs) -> None:
        self._log(logging.ERROR, message, **kwargs)

    async def critical(self, message: str, **kwargs) -> None:
        self._log(logging.CRITICAL, message, **kwargs)