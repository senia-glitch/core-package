"""Реестр сценариев для регистрации и получения сценариев по имени."""

import importlib.metadata
import logging
from typing import Dict, Type, Any
from .base_scenario import BaseScenario

logger = logging.getLogger(__name__)


class ScenarioRegistry:
    """Реестр сценариев."""

    _scenarios: Dict[str, Type[BaseScenario]] = {}
    _autodiscovered = False

    @classmethod
    def register(cls, name: str, scenario_cls: Type[BaseScenario]) -> None:
        if name in cls._scenarios:
            raise ValueError(f"Scenario '{name}' already registered")
        cls._scenarios[name] = scenario_cls

    @classmethod
    def get(cls, name: str, deps: Dict[str, Any]) -> BaseScenario:
        scenario_cls = cls._scenarios.get(name)
        if not scenario_cls:
            raise ValueError(f"Scenario '{name}' not registered")
        return scenario_cls(**deps)

    @classmethod
    def autodiscover(cls) -> None:
        """Автоматически обнаруживает и регистрирует сценарии через entry points."""
        if cls._autodiscovered:
            return
        cls._autodiscovered = True
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                # Python 3.10+
                core_entries = entry_points.select(group='core.scenarios')
            else:
                # Python 3.8/3.9
                core_entries = entry_points.get('core.scenarios', [])
        except Exception as e:
            logger.warning("Failed to load entry points: %s", e)
            return

        for entry in core_entries:
            try:
                scenario_cls = entry.load()
                if entry.name not in cls._scenarios:
                    cls.register(entry.name, scenario_cls)
            except Exception as e:
                logger.warning(
                    "Failed to load scenario from entry point '%s': %s",
                    entry.name, e,
                )

    @classmethod
    def list_scenarios(cls) -> Dict[str, Type[BaseScenario]]:
        return cls._scenarios.copy()


# Автоматически запускаем автодискаверинг при импорте модуля
ScenarioRegistry.autodiscover()