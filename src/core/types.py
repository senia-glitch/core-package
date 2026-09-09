"""Общие типы и утилиты типов."""

from typing import Union, Dict, Any

# Идентификатор может быть int или str
ID = Union[int, str]

# JSON-совместимый тип
JSON = Dict[str, Any]