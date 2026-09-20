# src/core/base_scenario.py
"""Базовый класс для всех бизнес-сценариев."""

import inspect
from abc import ABC, abstractmethod
from typing import Any, Optional
from .interfaces import IDatabase, ICache, ILogger, IMetrics


class BaseScenario(ABC):
    """Абстрактный базовый класс для сценариев.

    Сценарий получает зависимости через конструктор и реализует метод execute.
    Для сбора метрик используйте декоратор @track_metrics над методом execute
    или @tracked_scenario над классом.

    При наследовании автоматически проверяется наличие метода
    ``execute(self, dto)`` — ошибка возникает на этапе импорта, а не при
    первом вызове.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Пропускаем сам BaseScenario и его промежуточные абстрактные классы
        if getattr(cls, "__abstractmethods__", None):
            return
        # Проверяем, определён ли execute в самом классе (не унаследован)
        if "execute" not in cls.__dict__:
            # Ищем конкретный execute в родителях (не абстрактный из BaseScenario)
            for base in cls.__mro__[1:]:
                if base is BaseScenario:
                    continue
                if "execute" in base.__dict__:
                    break
            else:
                raise TypeError(
                    f"Класс {cls.__name__} не определяет метод execute(self, dto). "
                    f"Добавьте async def execute(self, dto) в класс."
                )
        execute = cls.__dict__.get("execute")
        if execute is None:
            execute = getattr(cls, "execute", None)
        if execute is None:
            return
        try:
            sig = inspect.signature(execute)
        except (ValueError, TypeError):
            return
        params = [
            p
            for p in sig.parameters.values()
            if p.name != "self"
            and p.kind
            not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ]
        if not params:
            raise TypeError(
                f"Метод execute в {cls.__name__} не принимает аргумент dto. "
                f"Ожидалась сигнатура execute(self, dto), "
                f"получена execute(self)."
            )

    def __init__(
        self,
        db: IDatabase,
        cache: Optional[ICache] = None,
        logger: Optional[ILogger] = None,
        metrics: Optional[IMetrics] = None,
    ):
        self._db = db
        self._cache = cache
        self._logger = logger
        self._metrics = metrics

    @abstractmethod
    async def execute(self, dto: Any) -> Any:
        ...