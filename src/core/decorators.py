# src/core/decorators.py

import time
import functools
from typing import Any, Callable, TypeVar, Awaitable
from .metrics import get_metrics

T = TypeVar('T')


def track_metrics(scenario_name: str) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Декоратор для отслеживания метрик выполнения сценария.

    Устанавливает атрибут `_core_metrics_wrapped` на обёрнутую функцию.
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            instance = args[0] if args else None
            metrics = getattr(instance, '_metrics', None) or get_metrics()

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
                    await metrics.record(scenario_name, elapsed_ms, scenario=scenario_name, error=error)
                except Exception:
                    # fail-open: игнорируем ошибки метрик
                    pass

        # Помечаем, что функция уже обёрнута
        wrapper._core_metrics_wrapped = True
        return wrapper
    return decorator


def tracked_scenario(name: str):
    """
    Декоратор класса, который автоматически оборачивает метод execute
    в декоратор track_metrics с указанным именем.
    """
    def decorator(cls):
        original_execute = cls.execute
        cls.execute = track_metrics(name)(original_execute)
        # Устанавливаем флаг, чтобы BaseScenario не оборачивал повторно
        cls.execute._core_metrics_wrapped = True
        return cls
    return decorator