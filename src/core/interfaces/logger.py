"""Интерфейс для логирования."""

from typing import Protocol


class ILogger(Protocol):
    """Асинхронный интерфейс для логирования."""

    async def debug(self, message: str, **kwargs) -> None:
        """Логирует сообщение уровня DEBUG."""
        ...

    async def info(self, message: str, **kwargs) -> None:
        """Логирует сообщение уровня INFO."""
        ...

    async def warning(self, message: str, **kwargs) -> None:
        """Логирует сообщение уровня WARNING."""
        ...

    async def error(self, message: str, **kwargs) -> None:
        """Логирует сообщение уровня ERROR."""
        ...

    async def critical(self, message: str, **kwargs) -> None:
        """Логирует сообщение уровня CRITICAL."""
        ...