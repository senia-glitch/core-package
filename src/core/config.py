# src/core/config.py
"""Загрузка конфигурации из переменных окружения.

Поиск файла .core-package.env выполняется:
1. По явному пути из переменной окружения CORE_ENV_PATH.
2. В текущей директории и всех родительских (до корня файловой системы).
Если файл не найден, используются только переменные окружения.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


def _find_env_file() -> Optional[Path]:
    """Ищет .core-package.env начиная с текущей директории вверх."""
    explicit = os.getenv("CORE_ENV_PATH")
    if explicit:
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() else None

    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        candidate = parent / ".core-package.env"
        if candidate.exists():
            return candidate
    return None


env_file = _find_env_file()
if env_file and os.getenv("CORE_SKIP_DOTENV", "").lower() not in ("true", "1", "yes"):
    load_dotenv(env_file)


def get_env_var(name: str, default: str = "") -> str:
    """Возвращает значение переменной окружения или значение по умолчанию.

    Args:
        name: Имя переменной.
        default: Значение по умолчанию.

    Returns:
        Значение переменной или default.
    """
    return os.getenv(name, default)


def get_env_bool(name: str, default: bool = False) -> bool:
    """Возвращает булево значение переменной окружения.

    Принимает значения: true, 1, yes, on (регистронезависимо).

    Args:
        name: Имя переменной.
        default: Значение по умолчанию.

    Returns:
        True или False.
    """
    val = os.getenv(name, "").lower()
    if val in ("true", "1", "yes", "on"):
        return True
    elif val in ("false", "0", "no", "off"):
        return False
    return default


def get_env_int(name: str, default: int = 0) -> int:
    """Возвращает целочисленное значение переменной окружения.

    Args:
        name: Имя переменной.
        default: Значение по умолчанию.

    Returns:
        Целое число или default при ошибке.
    """
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def get_env_float(name: str, default: float = 0.0) -> float:
    """Возвращает число с плавающей точкой из переменной окружения.

    Args:
        name: Имя переменной.
        default: Значение по умолчанию.

    Returns:
        Число или default при ошибке.
    """
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default