"""Утилиты безопасности: хеширование паролей (bcrypt) и JWT.

Основано на исходном коде core/utils/security.py проекта Proj.
"""

import asyncio
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Optional

import jwt
import bcrypt
from ..config import (
    get_env_int,
    get_env_var,
)

# Polyfill: asyncio.to_thread добавлен в Python 3.9
if sys.version_info >= (3, 9):
    _to_thread = asyncio.to_thread
else:
    async def _to_thread(func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

# Загрузка конфигурации из переменных окружения
JWT_SECRET = get_env_var("CORE_JWT_SECRET", "change-me-in-production")
ACCESS_TOKEN_MINUTES = get_env_int("CORE_ACCESS_TOKEN_MINUTES", 15)
REFRESH_TOKEN_DAYS = get_env_int("CORE_REFRESH_TOKEN_DAYS", 30)
BCRYPT_ROUNDS = get_env_int("CORE_BCRYPT_ROUNDS", 12)


@dataclass
class TokenInfo:
    """Результат декодирования access токена."""
    user_id: int
    role: str


# ========== Хеширование паролей ==========

async def hash_password(password: str) -> str:
    """Асинхронно хеширует пароль с помощью bcrypt.

    Args:
        password: Пароль в открытом виде.

    Returns:
        Хеш пароля в виде строки.
    """
    return await _to_thread(_hash_password_sync, password)


def _hash_password_sync(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    ).decode()


async def verify_password(password: str, hashed: str) -> bool:
    """Асинхронно проверяет пароль на соответствие хешу.

    Args:
        password: Пароль в открытом виде.
        hashed: Хеш для сравнения.

    Returns:
        True, если пароль совпадает.
    """
    return await _to_thread(_verify_password_sync, password, hashed)


def _verify_password_sync(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ========== JWT ==========

def create_access_token(user_id: int, role: str, secret: Optional[str] = None, expires_in: Optional[int] = None) -> str:
    """Создаёт access-токен.

    Args:
        user_id: ID пользователя.
        role: Роль пользователя.
        secret: Секрет для подписи (если None, используется глобальный).
        expires_in: Время жизни в минутах (если None, используется глобальное).

    Returns:
        JWT-токен в виде строки.
    """
    secret = secret if secret is not None else JWT_SECRET
    expires_in = expires_in if expires_in is not None else ACCESS_TOKEN_MINUTES
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_in * 60,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(user_id: int, secret: Optional[str] = None, expires_in: Optional[int] = None) -> str:
    """Создаёт refresh-токен.

    Args:
        user_id: ID пользователя.
        secret: Секрет для подписи (если None, используется глобальный).
        expires_in: Время жизни в днях (если None, используется глобальное).

    Returns:
        JWT-токен в виде строки.
    """
    secret = secret if secret is not None else JWT_SECRET
    expires_in = expires_in if expires_in is not None else REFRESH_TOKEN_DAYS
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_in * 86400,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: Optional[str] = None) -> dict:
    """Декодирует JWT-токен.

    Args:
        token: JWT-токен.
        secret: Секрет для верификации (если None, используется глобальный).

    Returns:
        Словарь с данными токена.

    Raises:
        jwt.InvalidTokenError: Если токен недействителен.
    """
    secret = secret if secret is not None else JWT_SECRET
    return jwt.decode(token, secret, algorithms=["HS256"])


def extract_token_info(token: str, secret: Optional[str] = None) -> TokenInfo:
    """Извлекает user_id и роль из access токена.

    Args:
        token: Access-токен.
        secret: Секрет (опционально).

    Returns:
        TokenInfo с user_id и role.

    Raises:
        jwt.InvalidTokenError: Если токен недействителен или payload некорректен.
    """
    payload = decode_token(token, secret)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError) as e:
        raise jwt.InvalidTokenError(f"Invalid token payload: {e}") from e
    return TokenInfo(user_id=user_id, role=payload.get("role", ""))