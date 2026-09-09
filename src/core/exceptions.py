"""Исключения core-package."""

from typing import Optional


class CoreError(Exception):
    """Базовое исключение с необязательными кодом и HTTP-статусом."""

    def __init__(self, message: str = "", *, code: Optional[int] = None, http_status: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status


class NotFoundError(CoreError):
    """Исключение, выбрасываемое когда сущность не найдена."""
    def __init__(self, message: str = "Not found", **kwargs):
        super().__init__(message, code=kwargs.pop('code', None), http_status=404, **kwargs)


class ValidationError(CoreError):
    """Исключение, выбрасываемое при ошибке валидации данных."""
    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(message, code=kwargs.pop('code', None), http_status=422, **kwargs)


class ConflictError(CoreError):
    """Исключение, выбрасываемое при конфликте (например, дубликат)."""
    def __init__(self, message: str = "Conflict", **kwargs):
        super().__init__(message, code=kwargs.pop('code', None), http_status=409, **kwargs)