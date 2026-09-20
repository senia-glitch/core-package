"""core-package: платформа для построения бизнес-сценариев.

Экспортирует основные компоненты:
- Интерфейсы: IDatabase, ICache, ILogger, IMetrics
- BaseScenario, ScenarioRegistry
- Исключения, утилиты
- Встроенные логгер, метрики и кеш
- Декораторы: track_metrics, tracked_scenario, register_scenario
- Точку входа: start_core, run, get_scenario и get-функции для зависимостей
"""

__version__ = "0.3.0"

from .interfaces import IDatabase, ICache, ILogger, IMetrics
from .base_scenario import BaseScenario
from .scenario_registry import ScenarioRegistry, ScenarioEntry
from .exceptions import CoreError, NotFoundError, ValidationError, ConflictError
from .dto import BaseDTO
from . import utils
from .logger import ConsoleLogger
from .metrics import InMemoryMetrics, get_metrics, reset_metrics
from .cache import TTLCache, FIFOCache, InMemoryCache
from .types import ID, JSON
from .decorators import track_metrics, tracked_scenario, register_scenario
from .startup import (
    start_core,
    run,
    get_scenario,
    get_db,
    get_cache,
    get_logger,
    get_core_metrics,
    reset_core,
    shutdown_core,
)

__all__ = [
    "IDatabase",
    "ICache",
    "ILogger",
    "IMetrics",
    "BaseScenario",
    "ScenarioRegistry",
    "ScenarioEntry",
    "CoreError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "BaseDTO",
    "utils",
    "ConsoleLogger",
    "InMemoryMetrics",
    "TTLCache",
    "FIFOCache",
    "InMemoryCache",
    "ID",
    "JSON",
    "get_metrics",
    "reset_metrics",
    "track_metrics",
    "tracked_scenario",
    "register_scenario",
    # startup
    "start_core",
    "run",
    "get_scenario",
    "get_db",
    "get_cache",
    "get_logger",
    "get_core_metrics",
    "reset_core",
    "shutdown_core",
]