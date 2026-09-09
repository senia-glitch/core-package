"""Интерфейсы для внешних зависимостей."""

from .database import IDatabase
from .cache import ICache
from .logger import ILogger
from .metrics import IMetrics
from .transactional_database import ITransactionalDatabase

__all__ = ["IDatabase", "ICache", "ILogger", "IMetrics", "ITransactionalDatabase"]