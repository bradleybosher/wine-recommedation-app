"""Password hashing and JWT signing — pure utilities, no FastAPI imports.

Kept FastAPI-free so it can be unit-tested in isolation and reused outside
the request lifecycle (CLI tools, migrations, tests).
"""
from __future__ import annotations

import base64
import hashlib
import time
from typing import Any

import jwt
from passlib.context import CryptContext

from bootstrap import JWT_ALGORITHM, JWT_EXPIRY_DAYS, JWT_SECRET

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prehash(plaintext: str) -> str:
    # bcrypt truncates at 72 bytes; SHA-256 → base64 keeps input to 44 bytes
    digest = hashlib.sha256(plaintext.encode()).digest()
    return base64.b64encode(digest).decode()


def hash_password(plaintext: str) -> str:
    return _pwd_context.hash(_prehash(plaintext))


def verify_password(plaintext: str, password_hash: str) -> bool:
    return _pwd_context.verify(_prehash(plaintext), password_hash)


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
