"""Общие валидаторы.

Основано на исходном коде core/utils/validators.py.
"""

import re
from typing import Any

from ..exceptions import ValidationError


def validate_pagination(limit: int, offset: int) -> None:
    """Проверяет корректность параметров пагинации.

    Args:
        limit: Количество записей (должно быть от 1 до 1000).
        offset: Смещение (должно быть >= 0).

    Raises:
        ValidationError: Если параметры некорректны.
    """
    if limit < 1 or limit > 1000:
        raise ValidationError("limit must be between 1 and 1000")
    if offset < 0:
        raise ValidationError("offset must be >= 0")


def validate_required(value: Any, field_name: str) -> None:
    """Проверяет, что обязательное поле не None и не пустая строка.

    Args:
        value: Значение поля.
        field_name: Имя поля для сообщения об ошибке.

    Raises:
        ValidationError: Если поле отсутствует или пустое.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"{field_name} is required")


def validate_email(email: str) -> None:
    """Проверяет, что строка является корректным email-адресом.

    Args:
        email: Email для проверки.

    Raises:
        ValidationError: Если email не соответствует формату.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email: {email}")