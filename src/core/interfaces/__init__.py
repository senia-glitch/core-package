"""Интерфейсы для внешних зависимостей."""

from .database import IDatabase
from .cache import ICache
from .logger import ILogger
from .metrics import IMetrics

__all__ = ["IDatabase", "ICache", "ILogger", "IMetrics"]