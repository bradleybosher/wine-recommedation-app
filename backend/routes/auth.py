"""Auth routes: register, login, me.

Open self-registration. First registered user inherits the orphan default
profile created during legacy data migration. Subsequent users get a fresh
empty default profile.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

import cache
from auth import create_access_token, hash_password, verify_password
from dependencies import get_current_user
from models import (
    AuthMeResponse,
    LoginRequest,
    Profile,
    RegisterRequest,
    TokenResponse,
    User,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("sommelier.api")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> TokenResponse:
    email = payload.email.lower().strip()
    if cache.get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user_row = cache.create_user(email=email, password_hash=hash_password(payload.password))
    user_id = user_row["id"]

    claimed_id = cache.claim_orphan_profile(user_id)
    if claimed_id:
        logger.info("register: user %s claimed orphan profile %s", user_id, claimed_id)
        profile_row = cache.get_profile(claimed_id)
    else:
        profile_row = cache.create_profile(user_id=user_id, name="My Palate", is_default=True)
        logger.info("register: created fresh default profile %s for user %s", profile_row["id"], user_id)

    return TokenResponse(
        access_token=create_access_token(user_id),
        user=User.model_validate(user_row),
        profile=Profile.model_validate(profile_row),
    )


@router.post("/login")
def login(payload: LoginRequest) -> TokenResponse:
    email = payload.email.lower().strip()
    user_row = cache.get_user_by_email(email)
    if not user_row or not verify_password(payload.password, user_row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    profiles = cache.list_profiles_for_user(user_row["id"])
    if not profiles:
        # Recover gracefully if a user somehow has no profiles (shouldn't happen post-register).
        profile_row = cache.create_profile(user_id=user_row["id"], name="My Palate", is_default=True)
    else:
        profile_row = next((p for p in profiles if p["is_default"]), profiles[0])

    return TokenResponse(
        access_token=create_access_token(user_row["id"]),
        user=User.model_validate(user_row),
        profile=Profile.model_validate(profile_row),
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> AuthMeResponse:
    profiles = cache.list_profiles_for_user(user.id)
    return AuthMeResponse(
        user=user,
        profiles=[Profile.model_validate(p) for p in profiles],
    )
