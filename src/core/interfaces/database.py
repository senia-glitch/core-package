"""Интерфейс для работы с базой данных."""

from typing import Any, Dict, List, Optional, Protocol


class IDatabase(Protocol):
    """Асинхронный интерфейс для доступа к базе данных."""

    async def create(self, entity: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Создаёт запись в таблице entity.

        Args:
            entity: Имя таблицы.
            data: Данные для вставки (словарь полей и значений).
            **kwargs: Дополнительные параметры (например, channel, timeout).

        Returns:
            Созданная запись в виде словаря.

        Raises:
            Exception: При ошибке выполнения запроса.
        """
        ...

    async def read(self, entity: str, id: Any, **kwargs) -> Optional[Dict[str, Any]]:
        """Читает запись по первичному ключу.

        Args:
            entity: Имя таблицы.
            id: Значение первичного ключа.
            **kwargs: Дополнительные параметры.

        Returns:
            Запись в виде словаря или None, если не найдена.
        """
        ...

    async def update(self, entity: str, id: Any, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Обновляет запись по первичному ключу.

        Args:
            entity: Имя таблицы.
            id: Значение первичного ключа.
            data: Данные для обновления.
            **kwargs: Дополнительные параметры.

        Returns:
            Обновлённая запись.

        Raises:
            Exception: Если запись не найдена или ошибка выполнения.
        """
        ...

    async def delete(self, entity: str, id: Any, **kwargs) -> bool:
        """Удаляет запись по первичному ключу.

        Args:
            entity: Имя таблицы.
            id: Значение первичного ключа.
            **kwargs: Дополнительные параметры.

        Returns:
            True, если запись была удалена, иначе False.
        """
        ...

    async def custom(self, sql: str, params: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """Выполняет произвольный SQL-запрос.

        Args:
            sql: SQL-запрос с плейсхолдерами (например, :id).
            params: Словарь параметров для подстановки.
            **kwargs: Дополнительные параметры.

        Returns:
            Список записей в виде словарей.

        Raises:
            Exception: При ошибке выполнения запроса.
        """
        ...