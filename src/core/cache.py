# src/core/cache.py
"""In-memory реализация ICache с TTL, ограничением размера и потокобезопасностью."""

import asyncio
import time
from typing import Any, Optional

from .interfaces import ICache


class InMemoryCache(ICache):
    """Простой in-memory кеш с TTL, ограничением размера и защитой от гонок."""

    def __init__(self, ttl_seconds: int = 60, max_size: int = 1000):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str, **kwargs) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                expires_at, value = self._cache[key]
                if time.monotonic() < expires_at:
                    return value
                del self._cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, **kwargs) -> None:
        async with self._lock:
            if len(self._cache) >= self._max_size:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest]
            ttl_seconds = ttl if ttl is not None else self._ttl
            expires_at = time.monotonic() + ttl_seconds
            self._cache[key] = (expires_at, value)

    async def delete(self, key: str, **kwargs) -> None:
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self, **kwargs) -> None:
        async with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)