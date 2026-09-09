# tests/test_interfaces.py
"""Тесты интерфейсов core-package."""

import pytest
from core.interfaces import IDatabase, ICache, ILogger, IMetrics, ITransactionalDatabase


def test_idatabase_protocol():
    assert hasattr(IDatabase, "create")
    assert hasattr(IDatabase, "read")
    assert hasattr(IDatabase, "update")
    assert hasattr(IDatabase, "delete")
    assert hasattr(IDatabase, "custom")


def test_icache_protocol():
    assert hasattr(ICache, "get")
    assert hasattr(ICache, "set")
    assert hasattr(ICache, "delete")
    assert hasattr(ICache, "clear")


def test_ilogger_protocol():
    assert hasattr(ILogger, "debug")
    assert hasattr(ILogger, "info")
    assert hasattr(ILogger, "warning")
    assert hasattr(ILogger, "error")
    assert hasattr(ILogger, "critical")


def test_imetrics_protocol():
    assert hasattr(IMetrics, "record")
    assert hasattr(IMetrics, "increment")


def test_itransactional_database_protocol():
    # Проверяем наличие всех методов IDatabase
    for method in ["create", "read", "update", "delete", "custom"]:
        assert hasattr(ITransactionalDatabase, method)
    # Проверяем дополнительные методы транзакций
    assert hasattr(ITransactionalDatabase, "begin_transaction")
    assert hasattr(ITransactionalDatabase, "commit_transaction")
    assert hasattr(ITransactionalDatabase, "rollback_transaction")
    assert hasattr(ITransactionalDatabase, "transaction")