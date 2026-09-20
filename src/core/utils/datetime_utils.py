"""Утилиты для работы с датами и временем.

Основано на исходном коде core/utils/ (адаптировано).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def parse_iso_datetime(value: str) -> datetime:
    """Парсит ISO-строку в datetime.

    Поддерживает форматы:
    - "2026-01-01T10:00:00"
    - "2026-01-01 10:00:00"
    - с указанием часового пояса: "2026-01-01T10:00:00+03:00"

    Args:
        value: Строка с датой и временем.

    Returns:
        datetime (без учёта часового пояса, если не указан).

    Raises:
        ValueError: Если строка не соответствует формату.
    """
    s = value.replace(" ", "T")
    # fromisoformat не понимает "Z" на Python 3.8–3.10
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.fromisoformat(s + ":00")
        except ValueError:
            raise ValueError(f"Не удалось распарсить дату: {value}")
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def normalize_timezone(dt: datetime, offset_hours: int = 0) -> datetime:
    """Приводит datetime к заданному смещению (или к UTC).

    Args:
        dt: datetime (предполагается наивным или с UTC).
        offset_hours: Смещение в часах от UTC (положительное – восточнее).

    Returns:
        datetime с смещением offset_hours (наивный, без tzinfo).
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt + timedelta(hours=offset_hours)


def is_datetime_in_past(dt: datetime, now: Optional[datetime] = None) -> bool:
    """Проверяет, является ли datetime прошедшим.

    Args:
        dt: Проверяемый datetime.
        now: Текущее время (если None, используется datetime.now()).

    Returns:
        True, если dt < now.
    """
    if now is None:
        now = datetime.now()
    return dt < now


def format_iso(dt: datetime, with_timezone: bool = False) -> str:
    """Форматирует datetime в ISO-строку.

    Args:
        dt: datetime.
        with_timezone: Добавлять ли часовой пояс (UTC).

    Returns:
        Строка в формате "YYYY-MM-DDTHH:MM:SS" или с "Z" если with_timezone=True.

    Raises:
        ValueError: Если with_timezone=True, но datetime наивный (без tzinfo).
    """
    if with_timezone:
        if dt.tzinfo is None:
            raise ValueError(
                "Cannot add timezone to naive datetime. "
                "Use datetime with tzinfo or call normalize_timezone() first."
            )
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return dt.isoformat()