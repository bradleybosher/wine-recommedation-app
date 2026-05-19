"""FastAPI dependency injection for auth + active profile resolution.

Two deps:
  * ``get_current_user`` — extracts a Bearer JWT, decodes it, looks up the user.
  * ``get_current_profile`` — reads ``X-Profile-Id`` header, validates ownership.

Routes that need only auth use the first. Routes that operate on profile data
(profile, inventory, recommend, history) use the second, which depends on the
first.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status

import cache
from auth import TokenError, decode_access_token
from models import Profile, User


def get_current_user(authorization: Optional[str] = Header(default=None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_access_token(token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    row = cache.get_user_by_id(user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return User.model_validate(row)


def get_current_profile(
    x_profile_id: Optional[str] = Header(default=None, alias="X-Profile-Id"),
    user: User = Depends(get_current_user),
) -> Profile:
    if not x_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Profile-Id header",
        )
    row = cache.get_profile(x_profile_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    if row["user_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile not owned by current user")
    return Profile.model_validate(row)
