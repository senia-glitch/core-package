# tests/test_interfaces.py
"""Тесты интерфейсов core-package."""

import inspect
from core.interfaces import IDatabase, ICache, ILogger, IMetrics


def test_idatabase_protocol():
    assert hasattr(IDatabase, "create")
    assert hasattr(IDatabase, "read")
    assert hasattr(IDatabase, "update")
    assert hasattr(IDatabase, "delete")
    assert hasattr(IDatabase, "query")


def test_idatabase_query_signature():
    sig = inspect.signature(IDatabase.query)
    params = list(sig.parameters.keys())
    assert params[0] == "self"
    assert params[1] == "description"
    assert params[2] == "params"


def test_icache_protocol():
    assert hasattr(ICache, "get")
    assert hasattr(ICache, "set")
    assert hasattr(ICache, "delete")
    assert hasattr(ICache, "clear")


def test_icache_get_signature():
    sig = inspect.signature(ICache.get)
    params = list(sig.parameters.keys())
    assert "key" in params


def test_ilogger_protocol():
    assert hasattr(ILogger, "debug")
    assert hasattr(ILogger, "info")
    assert hasattr(ILogger, "warning")
    assert hasattr(ILogger, "error")
    assert hasattr(ILogger, "critical")


def test_ilogger_methods_have_message_param():
    for method_name in ("debug", "info", "warning", "error", "critical"):
        method = getattr(ILogger, method_name)
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "message" in params, f"ILogger.{method_name} missing 'message' param"


def test_imetrics_protocol():
    assert hasattr(IMetrics, "record")
    assert hasattr(IMetrics, "increment")


def test_imetrics_record_signature():
    sig = inspect.signature(IMetrics.record)
    params = list(sig.parameters.keys())
    assert "name" in params
    assert "value" in params
