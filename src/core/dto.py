"""Базовые DTO для сценариев."""

from typing import Optional
from pydantic import BaseModel, Field


class BaseDTO(BaseModel):
    """Базовый DTO с общими полями.

    Может быть расширен в конкретных сценариях.
    """

    access_token: Optional[str] = Field(
        default=None,
        description="Токен доступа (используется для аутентификации)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Количество записей на страницу"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Смещение для пагинации"
    )