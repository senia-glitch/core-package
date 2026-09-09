# tests/test_dto.py
"""Тесты базового DTO."""

from core import BaseDTO


def test_base_dto_defaults():
    dto = BaseDTO()
    assert dto.access_token is None
    assert dto.limit == 100
    assert dto.offset == 0


def test_base_dto_custom_values():
    dto = BaseDTO(access_token="test_token", limit=50, offset=10)
    assert dto.access_token == "test_token"
    assert dto.limit == 50
    assert dto.offset == 10


def test_base_dto_validation():
    # limit должен быть от 1 до 1000
    dto = BaseDTO(limit=500)
    assert dto.limit == 500

    # Проверяем, что Pydantic сам валидирует
    import pytest
    with pytest.raises(ValueError):
        BaseDTO(limit=0)
    with pytest.raises(ValueError):
        BaseDTO(limit=1001)
    with pytest.raises(ValueError):
        BaseDTO(offset=-1)