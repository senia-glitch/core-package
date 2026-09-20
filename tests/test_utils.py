"""Тесты утилит core-package."""

import pytest
from datetime import datetime, timezone
from core.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_token_info,
    parse_iso_datetime,
    normalize_timezone,
    is_datetime_in_past,
    format_iso,
    validate_pagination,
    validate_required,
    validate_email,
)
from core.exceptions import ValidationError


@pytest.mark.asyncio
async def test_password_hashing():
    password = "test123"
    hashed = await hash_password(password)
    assert hashed != password
    assert await verify_password(password, hashed) is True
    assert await verify_password("wrong", hashed) is False


def test_create_access_token_and_decode():
    token = create_access_token(user_id=42, role="admin", secret="mysecret", expires_in=5)
    payload = decode_token(token, secret="mysecret")
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_create_refresh_token_and_decode():
    token = create_refresh_token(user_id=42, secret="mysecret", expires_in=1)
    payload = decode_token(token, secret="mysecret")
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_extract_token_info():
    token = create_access_token(user_id=7, role="student", secret="secret")
    info = extract_token_info(token, secret="secret")
    assert info.user_id == 7
    assert info.role == "student"


def test_decode_token_invalid():
    with pytest.raises(Exception):
        decode_token("invalid.token.string", secret="secret")


def test_parse_iso_datetime():
    dt = parse_iso_datetime("2026-01-01T10:00:00")
    assert dt.year == 2026
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 10
    assert dt.minute == 0


def test_parse_iso_datetime_with_space():
    """Поддержка разделителя пробелом вместо 'T'."""
    dt = parse_iso_datetime("2026-01-01 10:00:00")
    assert dt.hour == 10
    assert dt.minute == 0


def test_parse_iso_datetime_without_seconds():
    """Поддержка формата без секунд (добавляется :00)."""
    dt = parse_iso_datetime("2026-01-01T10:00")
    assert dt.hour == 10
    assert dt.minute == 0
    assert dt.second == 0


def test_parse_iso_datetime_invalid():
    with pytest.raises(ValueError):
        parse_iso_datetime("invalid")


def test_parse_iso_datetime_with_timezone():
    dt = parse_iso_datetime("2026-01-01T10:00:00+03:00")
    # Должен быть приведён к UTC
    assert dt.hour == 7  # 10:00 +03:00 = 07:00 UTC


def test_normalize_timezone():
    dt = datetime(2026, 1, 1, 10, 0, 0)
    normalized = normalize_timezone(dt, offset_hours=3)
    assert normalized.hour == 13


def test_normalize_timezone_with_aware_datetime():
    """Если datetime уже содержит tzinfo, он приводится к UTC перед смещением."""
    dt = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    normalized = normalize_timezone(dt, offset_hours=3)
    assert normalized.hour == 13


def test_is_datetime_in_past():
    past = datetime(2000, 1, 1)
    now = datetime(2026, 1, 1)
    assert is_datetime_in_past(past, now) is True
    future = datetime(2030, 1, 1)
    assert is_datetime_in_past(future, now) is False


def test_is_datetime_in_past_without_now():
    """Проверяем вызов без явного now (используется текущее время)."""
    past = datetime(2000, 1, 1)
    assert is_datetime_in_past(past) is True
    future = datetime(2030, 1, 1)
    assert is_datetime_in_past(future) is False


def test_format_iso():
    dt = datetime(2026, 1, 1, 10, 0, 0)
    formatted = format_iso(dt)
    assert formatted == "2026-01-01T10:00:00"

    with pytest.raises(ValueError, match="naive datetime"):
        format_iso(dt, with_timezone=True)

    from datetime import timezone
    dt_utc = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    formatted_z = format_iso(dt_utc, with_timezone=True)
    assert formatted_z == "2026-01-01T10:00:00Z"


def test_parse_iso_datetime_with_z_suffix():
    """parse_iso_datetime корректно парсит 'Z' суффикс (совместимость с 3.8-3.10)."""
    from core.utils.datetime_utils import parse_iso_datetime
    dt = parse_iso_datetime("2026-01-01T10:00:00Z")
    assert dt.year == 2026
    assert dt.month == 1
    assert dt.hour == 10
    assert dt.tzinfo is None


def test_validate_pagination():
    validate_pagination(10, 0)  # Должно пройти
    with pytest.raises(ValidationError):
        validate_pagination(0, 0)
    with pytest.raises(ValidationError):
        validate_pagination(1001, 0)
    with pytest.raises(ValidationError):
        validate_pagination(10, -1)


def test_validate_required():
    validate_required("test", "field")  # Должно пройти
    with pytest.raises(ValidationError):
        validate_required(None, "field")
    with pytest.raises(ValidationError):
        validate_required("", "field")


def test_validate_email():
    validate_email("test@example.com")  # Должно пройти
    with pytest.raises(ValidationError):
        validate_email("invalid")