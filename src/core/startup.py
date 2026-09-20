# src/core/startup.py
"""Точка входа ядра: инициализация и публичный доступ к сценариям.

Использование:

    from core import start_core, run

    async def main():
        await start_core(router=router, discover="my_project.scenarios")
        result = await run("greeting", GreetingDTO(user_id=1, name="Alice"))

Ядро хранится в модульном состоянии. Один экземпляр на процесс —
повторный вызов start_core без reset_core() бросает RuntimeError.
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from .base_scenario import BaseScenario
from .cache import InMemoryCache
from .interfaces import ICache, IDatabase, ILogger, IMetrics
from .logger import ConsoleLogger
from .metrics import InMemoryMetrics, reset_metrics
from .scenario_registry import ScenarioRegistry


@dataclass
class _CoreState:
    db: IDatabase
    cache: ICache
    logger: ILogger
    metrics: IMetrics


_state: Optional[_CoreState] = None


async def start_core(
    router: Any = None,
    *,
    db: Optional[IDatabase] = None,
    cache: Optional[ICache] = None,
    logger: Optional[ILogger] = None,
    metrics: Optional[IMetrics] = None,
    discover: Optional[str] = None,
) -> None:
    """Инициализирует ядро. Один вызов на процесс.

    Args:
        router: EventRouter из event-infra. Если передан — оборачивается
            в EventInfraDatabaseAdapter. Требует установленного event-infra.
        db: Готовая реализация IDatabase. Взаимоисключает с router.
        cache: Реализация ICache. По умолчанию InMemoryCache.
        logger: Реализация ILogger. По умолчанию ConsoleLogger.
        metrics: Реализация IMetrics. По умолчанию InMemoryMetrics.
        discover: Dotted-имя пакета со сценариями. Например,
            "my_project.scenarios". Будут импортированы все модули,
            декораторы @register_scenario сработают автоматически.

    Raises:
        RuntimeError: если ядро уже запущено.
        ValueError: если переданы и router, и db одновременно,
            или не передан ни один из них.
        ImportError: если передан router, но event-infra не установлен.
    """
    global _state

    if _state is not None:
        raise RuntimeError(
            "Ядро уже запущено. Для повторной инициализации вызовите reset_core()."
        )

    if db is not None and router is not None:
        raise ValueError("Передайте только один из параметров: db или router")

    if router is not None:
        try:
            from .adapters.event_infra import EventInfraDatabaseAdapter
        except ImportError as e:
            raise ImportError(
                "Для передачи router установите event-infra: "
                "pip install core-package[event-infra] "
                "или pip install git+https://github.com/senia-glitch/event-infra.git"
            ) from e
        db = EventInfraDatabaseAdapter(router)

    if db is None:
        raise ValueError(
            "Передайте router (event-infra) или db (IDatabase). "
            "Если event-infra не установлен — реализуйте свой IDatabase."
        )

    cache = cache if cache is not None else InMemoryCache()
    logger = logger if logger is not None else ConsoleLogger()
    metrics = metrics if metrics is not None else InMemoryMetrics()

    if os.getenv("CORE_ENV", "").lower() == "production":
        from .config import get_env_var
        secret = get_env_var("CORE_JWT_SECRET")
        if not secret or secret == "change-me-in-production":
            raise RuntimeError(
                "CORE_JWT_SECRET не установлен или не изменён. "
                "В production установите безопасный секрет в .core-package.env."
            )

    if discover:
        ScenarioRegistry.discover(discover)

    _state = _CoreState(db=db, cache=cache, logger=logger, metrics=metrics)


def _require_state() -> _CoreState:
    if _state is None:
        raise RuntimeError("Ядро не запущено. Сначала вызовите await start_core(...).")
    return _state


def get_scenario(name: str) -> BaseScenario:
    """Создаёт экземпляр сценария с уже внедрёнными зависимостями."""
    st = _require_state()
    return ScenarioRegistry.get(name, deps={
        "db": st.db,
        "cache": st.cache,
        "logger": st.logger,
        "metrics": st.metrics,
    })


async def run(name: str, dto: Any) -> Any:
    """Создаёт сценарий по имени и выполняет его."""
    return await get_scenario(name).execute(dto)


def get_db() -> IDatabase:
    """Возвращает активную реализацию IDatabase."""
    return _require_state().db


def get_cache() -> ICache:
    """Возвращает активную реализацию ICache."""
    return _require_state().cache


def get_logger() -> ILogger:
    """Возвращает активную реализацию ILogger."""
    return _require_state().logger


def get_core_metrics() -> IMetrics:
    """Возвращает активную реализацию IMetrics."""
    return _require_state().metrics


def reset_core() -> None:
    """Сбрасывает ядро и реестр сценариев.

    Предназначено для тестов и для случаев, когда нужно переинициализировать
    ядро в одном процессе (например, между тестами).

    Внутреннее состояние: ``_state`` — модульный синглтон, ``_scenarios`` —
    class-level dict в ``ScenarioRegistry``. Оба очищаются здесь.
    """
    global _state
    _state = None
    ScenarioRegistry._scenarios.clear()
    reset_metrics()


async def shutdown_core() -> None:
    """Корректно завершает работу ядра.

    Очищает кеш и сбрасывает состояние. Используйте при graceful shutdown.
    """
    global _state
    if _state is not None:
        if hasattr(_state.cache, "clear"):
            await _state.cache.clear()
    _state = None
    ScenarioRegistry._scenarios.clear()
    reset_metrics()