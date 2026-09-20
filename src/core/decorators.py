"""Декораторы для сценариев: регистрация и сбор метрик."""

import functools
import logging
import time
from typing import Any, Awaitable, Callable, Type, TypeVar

from .metrics import get_metrics

_logger = logging.getLogger(__name__)

T = TypeVar("T")
C = TypeVar("C", bound=type)


def track_metrics(
    scenario_name: str,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Декоратор для отслеживания метрик выполнения сценария.

    Устанавливает атрибут ``_core_metrics_wrapped`` на обёрнутую функцию,
    чтобы можно было избежать двойного оборачивания.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        if getattr(func, "_core_metrics_wrapped", False):
            return func

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            instance = args[0] if args else None
            metrics = getattr(instance, "_metrics", None) or get_metrics()

            start_time = time.perf_counter()
            error = False
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                error = True
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                try:
                    await metrics.record(
                        scenario_name,
                        elapsed_ms,
                        scenario=scenario_name,
                        error=error,
                    )
                except Exception as e:
                    # fail-open: логируем, но не ломаем вызов
                    _logger.warning("Failed to record metrics: %s", e)

        wrapper._core_metrics_wrapped = True
        return wrapper

    return decorator


def tracked_scenario(name: str):
    """Декоратор класса — оборачивает метод execute сбором метрик.

    Пример::

        @tracked_scenario("create_user")
        class CreateUserScenario(BaseScenario):
            async def execute(self, dto): ...
    """

    def decorator(cls: C) -> C:
        original_execute = cls.execute
        cls.execute = track_metrics(name)(original_execute)
        return cls

    return decorator


def register_scenario(name: str):
    """Декоратор класса — регистрирует сценарий в ScenarioRegistry.

    Срабатывает в момент импорта модуля, в котором объявлен класс.
    Чтобы модуль импортировался при старте приложения, вызовите
    ``ScenarioRegistry.discover("app.scenarios")``.

    Импорт ScenarioRegistry делается внутри функции, чтобы избежать
    проблем с порядком инициализации пакета.

    Пример::

        from core import BaseScenario, register_scenario

        @register_scenario("hello")
        class HelloScenario(BaseScenario):
            async def execute(self, dto): ...
    """

    def decorator(cls: C) -> C:
        from .scenario_registry import ScenarioRegistry

        ScenarioRegistry.register(name, cls)
        return cls

    return decorator