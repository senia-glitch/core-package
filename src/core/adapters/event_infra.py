# src/core/adapters/event_infra.py
"""Адаптер EventRouter (пакет event-infra) к интерфейсу IDatabase.

Импортируется лениво — только когда пользователь передаёт router
в start_core(). Если event-infra не установлен, модуль недоступен,
но сам core-package работает без него.
"""

import warnings
from typing import Any, Dict, List, Optional

from ..interfaces import IDatabase


class EventInfraDatabaseAdapter(IDatabase):
    """Связывает IDatabase с EventRouter."""

    def __init__(self, router: Any):
        self._router = router

    async def create(self, entity: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        channel = kwargs.get("channel", "write")
        resp = await self._router.create(entity, data, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message if resp.error else "Create failed")
        return resp.data[0] if resp.data else {}

    async def read(self, entity: str, id: Any, **kwargs) -> Optional[Dict[str, Any]]:
        channel = kwargs.get("channel", "read")
        resp = await self._router.read(entity, id, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message if resp.error else "Read failed")
        return resp.data[0] if resp.data else None

    async def update(self, entity: str, id: Any, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        channel = kwargs.get("channel", "write")
        resp = await self._router.update(entity, id, data, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message if resp.error else "Update failed")
        return resp.data[0] if resp.data else {}

    async def delete(self, entity: str, id: Any, **kwargs) -> bool:
        channel = kwargs.get("channel", "write")
        resp = await self._router.delete(entity, id, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message if resp.error else "Delete failed")
        return resp.count > 0

    async def query(self, description: str, params: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        channel = kwargs.get("channel", "read")
        resp = await self._router.custom(description, params, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message if resp.error else "Query failed")
        result: List[Dict[str, Any]] = []
        for item in resp.data or []:
            row = item.get("row")
            if row is None:
                continue
            if hasattr(row, "_mapping"):
                result.append(dict(row._mapping))
            elif isinstance(row, dict):
                result.append(row)
            else:
                result.append({"value": row})
        return result

    async def custom(self, sql: str, params: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """Deprecated: используйте query()."""
        warnings.warn(
            "custom() deprecated, use query()",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.query(sql, params, **kwargs)