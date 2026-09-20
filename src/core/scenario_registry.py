"""Реестр сценариев для регистрации и получения сценариев по имени."""

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from .base_scenario import BaseScenario

logger = logging.getLogger(__name__)


@dataclass
class ScenarioEntry:
    """Метаданные зарегистрированного сценария."""

    scenario_cls: Type[BaseScenario]
    response: Optional[Type] = None
    dto: Optional[Type] = None


class ScenarioRegistry:
    """Реестр сценариев.

    Сценарии регистрируются двумя способами:

    1. Явно — ``ScenarioRegistry.register("name", ScenarioClass)``.

    2. Через декоратор ``@register_scenario("name")`` — в момент импорта
       модуля со сценарием.

    Для загрузки всех сценариев из пакета используйте
    ``ScenarioRegistry.discover("app.scenarios")`` — он импортирует
    все модули внутри пакета, и декораторы сработают автоматически.
    """

    _scenarios: Dict[str, ScenarioEntry] = {}

    @classmethod
    def register(
        cls,
        name: str,
        scenario_cls: Type[BaseScenario],
        *,
        response: Optional[Type] = None,
        dto: Optional[Type] = None,
    ) -> None:
        """Регистрирует класс сценария под указанным именем.

        Args:
            name: Уникальное имя сценария.
            scenario_cls: Класс сценария (наследник BaseScenario).
            response: Модель ответа (Pydantic BaseModel). Если не передана —
                сценарий может вернуть любой тип.
            dto: Модель входных данных (Pydantic BaseModel). Если передана —
                run() будет валидировать входной объект.

        Raises:
            ValueError: если имя уже занято.
        """
        if name in cls._scenarios:
            raise ValueError(f"Scenario '{name}' already registered")
        cls._scenarios[name] = ScenarioEntry(
            scenario_cls=scenario_cls,
            response=response,
            dto=dto,
        )

    @classmethod
    def get(cls, name: str, deps: Dict[str, Any]) -> BaseScenario:
        """Создаёт экземпляр сценария с внедрёнными зависимостями.

        Args:
            name: Имя зарегистрированного сценария.
            deps: Словарь зависимостей для конструктора BaseScenario
                (обычно db, cache, logger, metrics).

        Raises:
            ValueError: если сценарий не зарегистрирован.
        """
        entry = cls._scenarios.get(name)
        if not entry:
            raise ValueError(f"Scenario '{name}' not registered")
        return entry.scenario_cls(**deps)

    @classmethod
    def get_entry(cls, name: str) -> ScenarioEntry:
        """Возвращает полную запись сценария (класс + метаданные).

        Raises:
            ValueError: если сценарий не зарегистрирован.
        """
        entry = cls._scenarios.get(name)
        if not entry:
            raise ValueError(f"Scenario '{name}' not registered")
        return entry

    @classmethod
    def get_response(cls, name: str) -> Optional[Type]:
        """Возвращает Response-модель сценария или None.

        Raises:
            ValueError: если сценарий не зарегистрирован.
        """
        return cls.get_entry(name).response

    @classmethod
    def get_dto(cls, name: str) -> Optional[Type]:
        """Возвращает DTO-модель сценария или None.

        Raises:
            ValueError: если сценарий не зарегистрирован.
        """
        return cls.get_entry(name).dto

    @classmethod
    def list_scenarios(cls) -> Dict[str, Type[BaseScenario]]:
        """Возвращает копию словаря зарегистрированных сценариев."""
        return {name: entry.scenario_cls for name, entry in cls._scenarios.items()}

    @classmethod
    def discover(cls, package: str) -> List[str]:
        """Импортирует все модули внутри пакета — срабатывают декораторы.

        Используется в точке входа приложения: достаточно один раз
        вызвать ``ScenarioRegistry.discover("app.scenarios")`` — и все
        сценарии, помеченные ``@register_scenario``, будут зарегистрированы.

        Args:
            package: Dotted-имя Python-пакета со сценариями,
                например ``"app.scenarios"``. Пакет должен быть
                импортируемым (обычно проект установлен через
                ``pip install -e .`` или его корень в sys.path).

        Returns:
            Список полных имён успешно импортированных модулей.
            Модули, которые не загрузились, попадают в лог как warning
            и в результат не включаются — одна ошибка не ломает старт.
        """
        try:
            pkg = importlib.import_module(package)
        except ImportError as e:
            logger.warning("Пакет '%s' не найден: %s", package, e)
            return []

        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            logger.warning("'%s' не является пакетом (нет __path__)", package)
            return []

        loaded: List[str] = []
        for _, name, _ in pkgutil.iter_modules(pkg_path):
            if name.startswith("_"):
                continue
            full = f"{package}.{name}"
            try:
                importlib.import_module(full)
                loaded.append(full)
            except Exception as e:
                logger.warning("Не удалось загрузить '%s': %s", full, e)

        return loaded