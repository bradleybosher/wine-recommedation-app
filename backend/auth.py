"""Password hashing and JWT signing — pure utilities, no FastAPI imports.

Kept FastAPI-free so it can be unit-tested in isolation and reused outside
the request lifecycle (CLI tools, migrations, tests).
"""
from __future__ import annotations

import time
from typing import Any

import jwt
from passlib.context import CryptContext

from bootstrap import JWT_ALGORITHM, JWT_EXPIRY_DAYS, JWT_SECRET

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plaintext: str) -> str:
    """Return a bcrypt hash of the password. Salt is embedded in the hash."""
    return _pwd_context.hash(plaintext)


def verify_password(plaintext: str, password_hash: str) -> bool:
    """Constant-time compare of plaintext against a stored bcrypt hash."""
    return _pwd_context.verify(plaintext, password_hash)


def create_access_token(user_id: str) -> str:
    """Sign a JWT carrying the user_id as `sub`. Lifetime from JWT_EXPIRY_DAYS env."""
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": now,
        "exp": now + JWT_EXPIRY_DAYS * 24 * 60 * 60,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TokenError(Exception):
    """Raised when a JWT is malformed, expired, or signed with the wrong key."""


def decode_access_token(token: str) -> str:
    """Verify a JWT and return the user_id. Raises TokenError on any failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as e:
        raise TokenError("Token expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenError("Invalid token") from e
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise TokenError("Token missing subject")
    return user_id
