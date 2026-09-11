# tests/test_types.py
"""Тесты типов core.types."""

from typing import Any, Dict, Union

from core.types import ID, JSON


def test_id_is_union_of_int_and_str():
    assert ID == Union[int, str]


def test_json_is_dict_of_str_any():
    assert JSON == Dict[str, Any]