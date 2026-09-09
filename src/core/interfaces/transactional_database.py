"""Расширенный интерфейс для БД с поддержкой транзакций."""

from typing import Protocol
from contextlib import AbstractAsyncContextManager

from .database import IDatabase


class ITransactionalDatabase(IDatabase, Protocol):
    """Асинхронный интерфейс для БД с поддержкой транзакций."""

    async def begin_transaction(self, **kwargs) -> None:
        """Начинает транзакцию."""
        ...

    async def commit_transaction(self, **kwargs) -> None:
        """Фиксирует транзакцию."""
        ...

    async def rollback_transaction(self, **kwargs) -> None:
        """Откатывает транзакцию."""
        ...

    def transaction(self, **kwargs) -> AbstractAsyncContextManager:
        """Возвращает асинхронный контекстный менеджер для транзакции."""
        ...