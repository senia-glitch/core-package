"""Реестр сценариев для регистрации и получения сценариев по имени."""

import importlib
import logging
import pkgutil
from typing import Any, Dict, List, Type

from .base_scenario import BaseScenario

logger = logging.getLogger(__name__)


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

    _scenarios: Dict[str, Type[BaseScenario]] = {}

    @classmethod
    def register(cls, name: str, scenario_cls: Type[BaseScenario]) -> None:
        """Регистрирует класс сценария под указанным именем.

        Raises:
            ValueError: если имя уже занято.
        """
        if name in cls._scenarios:
            raise ValueError(f"Scenario '{name}' already registered")
        cls._scenarios[name] = scenario_cls

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
        scenario_cls = cls._scenarios.get(name)
        if not scenario_cls:
            raise ValueError(f"Scenario '{name}' not registered")
        return scenario_cls(**deps)

    @classmethod
    def list_scenarios(cls) -> Dict[str, Type[BaseScenario]]:
        """Возвращает копию словаря зарегистрированных сценариев."""
        return cls._scenarios.copy()

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