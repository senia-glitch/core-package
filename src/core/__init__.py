"""core-package: платформа для построения бизнес-сценариев.

Экспортирует основные компоненты:
- Интерфейсы: IDatabase, ICache, ILogger, IMetrics, ITransactionalDatabase
- BaseScenario, ScenarioRegistry
- Исключения, утилиты
- Встроенные логгер, метрики и кеш
- Декораторы: track_metrics, tracked_scenario, register_scenario
"""

from .interfaces import IDatabase, ICache, ILogger, IMetrics, ITransactionalDatabase
from .base_scenario import BaseScenario
from .scenario_registry import ScenarioRegistry
from .exceptions import CoreError, NotFoundError, ValidationError, ConflictError
from .dto import BaseDTO
from . import utils
from .logger import ConsoleLogger
from .metrics import InMemoryMetrics, get_metrics
from .cache import InMemoryCache
from .decorators import track_metrics, tracked_scenario, register_scenario

__all__ = [
    "IDatabase",
    "ICache",
    "ILogger",
    "IMetrics",
    "ITransactionalDatabase",
    "BaseScenario",
    "ScenarioRegistry",
    "CoreError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "BaseDTO",
    "utils",
    "ConsoleLogger",
    "InMemoryMetrics",
    "InMemoryCache",
    "get_metrics",
    "track_metrics",
    "tracked_scenario",
    "register_scenario",
]