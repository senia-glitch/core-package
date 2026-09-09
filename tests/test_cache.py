# tests/test_cache.py
"""Тесты InMemoryCache."""

import asyncio
import pytest
from core import InMemoryCache


@pytest.mark.asyncio
async def test_cache_set_and_get():
    cache = InMemoryCache()
    await cache.set("key", "value")
    result = await cache.get("key")
    assert result == "value"


@pytest.mark.asyncio
async def test_cache_get_missing():
    cache = InMemoryCache()
    result = await cache.get("missing")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    cache = InMemoryCache()
    await cache.set("key", "value")
    await cache.delete("key")
    result = await cache.get("key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_clear():
    cache = InMemoryCache()
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.clear()
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert cache.size == 0


@pytest.mark.asyncio
async def test_cache_ttl():
    cache = InMemoryCache(ttl_seconds=1)
    await cache.set("key", "value")
    assert await cache.get("key") == "value"
    await asyncio.sleep(1.1)
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_cache_ttl_per_item():
    cache = InMemoryCache(ttl_seconds=60)
    await cache.set("key", "value", ttl=1)
    assert await cache.get("key") == "value"
    await asyncio.sleep(1.1)
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_cache_max_size():
    cache = InMemoryCache(max_size=2)
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)
    assert await cache.get("a") is None
    assert await cache.get("b") == 2
    assert await cache.get("c") == 3
    assert cache.size == 2


@pytest.mark.asyncio
async def test_cache_size_property():
    cache = InMemoryCache()
    assert cache.size == 0
    await cache.set("key", "value")
    assert cache.size == 1
    await cache.delete("key")
    assert cache.size == 0


@pytest.mark.asyncio
async def test_cache_has_lock():
    cache = InMemoryCache()
    assert hasattr(cache, "_lock")
    assert isinstance(cache._lock, asyncio.Lock)


@pytest.mark.asyncio
async def test_cache_concurrent_access():
    """Проверяем, что при конкурентном доступе не возникает ошибок."""
    cache = InMemoryCache(max_size=1000)
    async def worker(i):
        await cache.set(f"key_{i}", i)
        return await cache.get(f"key_{i}")

    results = await asyncio.gather(*(worker(i) for i in range(50)))
    for i, val in enumerate(results):
        assert val == i
    assert cache.size == 50