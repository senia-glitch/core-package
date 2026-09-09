"""Интерфейс для кеширования."""

from typing import Any, Optional, Protocol


class ICache(Protocol):
    """Асинхронный интерфейс для кеш-хранилища."""

    async def get(self, key: str, **kwargs) -> Optional[Any]:
        """Получает значение из кеша по ключу.

        Args:
            key: Ключ.
            **kwargs: Дополнительные параметры.

        Returns:
            Значение или None, если ключ отсутствует.
        """
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, **kwargs) -> None:
        """Сохраняет значение в кеш с опциональным TTL.

        Args:
            key: Ключ.
            value: Значение.
            ttl: Время жизни в секундах (опционально).
            **kwargs: Дополнительные параметры.
        """
        ...

    async def delete(self, key: str, **kwargs) -> None:
        """Удаляет запись из кеша по ключу.

        Args:
            key: Ключ.
            **kwargs: Дополнительные параметры.
        """
        ...

    async def clear(self, **kwargs) -> None:
        """Очищает весь кеш.

        Args:
            **kwargs: Дополнительные параметры.
        """
        ...