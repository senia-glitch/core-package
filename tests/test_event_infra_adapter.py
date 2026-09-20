# tests/test_event_infra_adapter.py
"""Тесты адаптера EventInfraDatabaseAdapter (без установки event-infra)."""

from types import SimpleNamespace

import pytest

from core.adapters.event_infra import EventInfraDatabaseAdapter


# ============================================================
# Фейки под Response и EventRouter
# ============================================================

class FakeResponse:
    """Имитация Response из event-infra."""

    def __init__(self, *, success=True, data=None, count=0, error_message=""):
        self.success = success
        self.data = data if data is not None else []
        self.count = count
        # error не None только если success=False И есть сообщение
        self.error = (
            SimpleNamespace(message=error_message)
            if (not success and error_message)
            else None
        )

class FakeRow:
    """Имитация asyncpg.Row с _mapping."""

    def __init__(self, mapping):
        self._mapping = mapping


class FakeRouter:
    """Имитация EventRouter — возвращает заданный Response."""

    def __init__(self, response):
        self._response = response
        self.calls = []

    async def create(self, entity, data, channel="write"):
        self.calls.append(("create", entity, data, channel))
        return self._response

    async def read(self, entity, id, channel="read"):
        self.calls.append(("read", entity, id, channel))
        return self._response

    async def update(self, entity, id, data, channel="write"):
        self.calls.append(("update", entity, id, data, channel))
        return self._response

    async def delete(self, entity, id, channel="write"):
        self.calls.append(("delete", entity, id, channel))
        return self._response

    async def custom(self, sql, params, channel="read"):
        self.calls.append(("custom", sql, params, channel))
        return self._response


# ============================================================
# create
# ============================================================

@pytest.mark.asyncio
async def test_create_success():
    row = {"id": 1, "name": "Alice"}
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[row])))
    result = await adapter.create("users", {"name": "Alice"})
    assert result == row


@pytest.mark.asyncio
async def test_create_success_empty_data():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[])))
    result = await adapter.create("users", {"name": "Alice"})
    assert result == {}


@pytest.mark.asyncio
async def test_create_failure_raises():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False, error_message="boom"))
    )
    with pytest.raises(Exception, match="boom"):
        await adapter.create("users", {"name": "Alice"})


@pytest.mark.asyncio
async def test_create_failure_no_error_message():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False))
    )
    with pytest.raises(Exception, match="Create failed"):
        await adapter.create("users", {})


# ============================================================
# read
# ============================================================

@pytest.mark.asyncio
async def test_read_success():
    row = {"id": 42, "name": "Bob"}
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[row])))
    result = await adapter.read("users", 42)
    assert result == row


@pytest.mark.asyncio
async def test_read_success_empty():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[])))
    result = await adapter.read("users", 999)
    assert result is None


@pytest.mark.asyncio
async def test_read_failure_raises():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False, error_message="not found"))
    )
    with pytest.raises(Exception, match="not found"):
        await adapter.read("users", 1)


@pytest.mark.asyncio
async def test_read_failure_no_error_message():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(success=False)))
    with pytest.raises(Exception, match="Read failed"):
        await adapter.read("users", 1)


# ============================================================
# update
# ============================================================

@pytest.mark.asyncio
async def test_update_success():
    row = {"id": 1, "name": "Charlie"}
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[row])))
    result = await adapter.update("users", 1, {"name": "Charlie"})
    assert result == row


@pytest.mark.asyncio
async def test_update_success_empty():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[])))
    result = await adapter.update("users", 1, {"name": "X"})
    assert result == {}


@pytest.mark.asyncio
async def test_update_failure_raises():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False, error_message="conflict"))
    )
    with pytest.raises(Exception, match="conflict"):
        await adapter.update("users", 1, {})


@pytest.mark.asyncio
async def test_update_failure_no_error_message():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(success=False)))
    with pytest.raises(Exception, match="Update failed"):
        await adapter.update("users", 1, {})


# ============================================================
# delete
# ============================================================

@pytest.mark.asyncio
async def test_delete_success_count_positive():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(count=1)))
    result = await adapter.delete("users", 1)
    assert result is True


@pytest.mark.asyncio
async def test_delete_success_count_zero():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(count=0)))
    result = await adapter.delete("users", 999)
    assert result is False


@pytest.mark.asyncio
async def test_delete_failure_raises():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False, error_message="fk violation"))
    )
    with pytest.raises(Exception, match="fk violation"):
        await adapter.delete("users", 1)


@pytest.mark.asyncio
async def test_delete_failure_no_error_message():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(success=False)))
    with pytest.raises(Exception, match="Delete failed"):
        await adapter.delete("users", 1)


# ============================================================
# custom
# ============================================================

@pytest.mark.asyncio
async def test_custom_success_with_mapping():
    """row с _mapping (как asyncpg.Row). custom() deprecated — проверяем warning."""
    rows = [{"row": FakeRow({"id": 1, "name": "Alice"})}]
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=rows)))
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        result = await adapter.custom("SELECT * FROM users", {}, channel="read")
    assert result == [{"id": 1, "name": "Alice"}]


@pytest.mark.asyncio
async def test_custom_success_with_dict():
    """row как обычный dict. custom() deprecated — проверяем warning."""
    rows = [{"row": {"id": 2, "name": "Bob"}}]
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=rows)))
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        result = await adapter.custom("SELECT * FROM users", {})
    assert result == [{"id": 2, "name": "Bob"}]


@pytest.mark.asyncio
async def test_custom_success_with_scalar():
    """row как скаляр (например COUNT(*)). custom() deprecated — проверяем warning."""
    rows = [{"row": 42}]
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=rows)))
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        result = await adapter.custom("SELECT COUNT(*) FROM users", {})
    assert result == [{"value": 42}]


@pytest.mark.asyncio
async def test_custom_skips_none_rows():
    """row=None пропускается. custom() deprecated — проверяем warning."""
    rows = [{"row": None}, {"row": {"id": 1}}]
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=rows)))
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        result = await adapter.custom("SELECT * FROM users", {})
    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_custom_empty_data():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=[])))
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        result = await adapter.custom("SELECT * FROM users", {})
    assert result == []


@pytest.mark.asyncio
async def test_custom_failure_raises():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False, error_message="syntax error"))
    )
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        with pytest.raises(Exception, match="syntax error"):
            await adapter.custom("BAD SQL", {})


@pytest.mark.asyncio
async def test_custom_failure_no_error_message():
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(success=False)))
    with pytest.warns(DeprecationWarning, match="custom\\(\\) deprecated"):
        with pytest.raises(Exception, match="Query failed"):
            await adapter.custom("BAD SQL", {})


# ============================================================
# query() — основной метод
# ============================================================

@pytest.mark.asyncio
async def test_query_success_with_mapping():
    """query() — row с _mapping (как asyncpg.Row)."""
    rows = [{"row": FakeRow({"id": 1, "name": "Alice"})}]
    adapter = EventInfraDatabaseAdapter(FakeRouter(FakeResponse(data=rows)))
    result = await adapter.query("SELECT * FROM users", {})
    assert result == [{"id": 1, "name": "Alice"}]


@pytest.mark.asyncio
async def test_query_failure_raises():
    adapter = EventInfraDatabaseAdapter(
        FakeRouter(FakeResponse(success=False, error_message="bad query"))
    )
    with pytest.raises(Exception, match="bad query"):
        await adapter.query("BAD QUERY", {})