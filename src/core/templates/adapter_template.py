"""Пример адаптера для инфраструктурного пакета event-infra.

Этот адаптер реализует интерфейс IDatabase для EventRouter из пакета event-infra.
"""

from typing import Any, Dict, List, Optional

from core.interfaces import IDatabase


class EventInfraDatabaseAdapter(IDatabase):
    """Адаптер, связывающий IDatabase с EventRouter."""

    def __init__(self, router):
        self._router = router

    async def create(self, entity: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        channel = kwargs.get("channel", "write")
        resp = await self._router.create(entity, data, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.data[0] if resp.data else {}

    async def read(self, entity: str, id: Any, **kwargs) -> Optional[Dict[str, Any]]:
        channel = kwargs.get("channel", "read")
        resp = await self._router.read(entity, id, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.data[0] if resp.data else None

    async def update(self, entity: str, id: Any, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        channel = kwargs.get("channel", "write")
        resp = await self._router.update(entity, id, data, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.data[0] if resp.data else {}

    async def delete(self, entity: str, id: Any, **kwargs) -> bool:
        channel = kwargs.get("channel", "write")
        resp = await self._router.delete(entity, id, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message)
        return resp.count > 0

    async def custom(self, sql: str, params: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        channel = kwargs.get("channel", "read")
        resp = await self._router.custom(sql, params, channel=channel)
        if not resp.success:
            raise Exception(resp.error.message)
        result = []
        for item in resp.data or []:
            row = item.get("row")
            if row is not None:
                if hasattr(row, '_mapping'):
                    result.append(dict(row._mapping))
                elif isinstance(row, dict):
                    result.append(row)
                else:
                    result.append({"value": row})
        return result