"""Profile management routes: list, create, rename, set-default, delete."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

import cache
from dependencies import get_current_user
from models import Profile, ProfileCreateRequest, ProfileUpdateRequest, User

router = APIRouter(prefix="/profiles", tags=["profiles"])
logger = logging.getLogger("sommelier.api")


def _load_owned_profile(profile_id: str, user: User) -> dict:
    row = cache.get_profile(profile_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    if row["user_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile not owned by current user")
    return row


@router.get("")
def list_profiles(user: User = Depends(get_current_user)) -> list[Profile]:
    rows = cache.list_profiles_for_user(user.id)
    return [Profile.model_validate(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreateRequest,
    user: User = Depends(get_current_user),
) -> Profile:
    has_existing = bool(cache.list_profiles_for_user(user.id))
    row = cache.create_profile(
        user_id=user.id,
        name=payload.name.strip(),
        is_default=not has_existing,
    )
    return Profile.model_validate(row)


@router.patch("/{profile_id}")
def update_profile(
    profile_id: str,
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
) -> Profile:
    _load_owned_profile(profile_id, user)

    if payload.name is not None:
        cache.update_profile(profile_id, name=payload.name.strip())
    if payload.is_default is True:
        cache.set_default_profile(profile_id, user.id)

    updated = cache.get_profile(profile_id)
    return Profile.model_validate(updated)


@router.delete("/{profile_id}")
def delete_profile(
    profile_id: str,
    user: User = Depends(get_current_user),
) -> dict:
    profile = _load_owned_profile(profile_id, user)
    owned = cache.list_profiles_for_user(user.id)
    if len(owned) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete your only profile",
        )
    was_default = profile["is_default"]
    cache.delete_profile(profile_id)

    if was_default:
        remaining = cache.list_profiles_for_user(user.id)
        if remaining:
            cache.set_default_profile(remaining[0]["id"], user.id)

    return {"id": profile_id, "deleted": True}
