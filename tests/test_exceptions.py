# tests/test_exceptions.py
"""Тесты исключений core-package."""

import pytest
from core import CoreError, NotFoundError, ValidationError, ConflictError


def test_exceptions_inheritance():
    assert issubclass(NotFoundError, CoreError)
    assert issubclass(ValidationError, CoreError)
    assert issubclass(ConflictError, CoreError)


def test_core_error_with_attributes():
    err = CoreError("Some error", code=100, http_status=500)
    assert str(err) == "Some error"
    assert err.code == 100
    assert err.http_status == 500

def test_core_error_defaults():
    err = CoreError("Default")
    assert err.code is None
    assert err.http_status is None

def test_not_found_error_defaults():
    err = NotFoundError("Not found")
    assert err.http_status == 404
    assert err.code is None

def test_not_found_error_with_code():
    err = NotFoundError("Not found", code=1102)
    assert err.code == 1102
    assert err.http_status == 404

def test_validation_error_defaults():
    err = ValidationError("Invalid")
    assert err.http_status == 422
    assert err.code is None

def test_conflict_error_defaults():
    err = ConflictError("Conflict")
    assert err.http_status == 409
    assert err.code is None

def test_exceptions_instantiation_with_raise():
    with pytest.raises(NotFoundError, match="Not found"):
        raise NotFoundError("Not found")
    with pytest.raises(ValidationError, match="Invalid"):
        raise ValidationError("Invalid")
    with pytest.raises(ConflictError, match="Conflict"):
        raise ConflictError("Conflict")