"""Интерфейс для сбора метрик."""

from typing import Protocol


class IMetrics(Protocol):
    """Асинхронный интерфейс для сбора метрик."""

    async def record(self, name: str, value: float, **labels) -> None:
        """Записывает числовое значение метрики (например, время выполнения).

        Args:
            name: Имя метрики.
            value: Числовое значение.
            **labels: Дополнительные метки (ключ-значение).
        """
        ...

    async def increment(self, name: str, **labels) -> None:
        """Увеличивает счётчик метрики на 1.

        Args:
            name: Имя метрики.
            **labels: Дополнительные метки.
        """
        ...