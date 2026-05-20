"""Insights route — palate drift suggestions derived from flight history."""

import logging

from fastapi import APIRouter, Depends

from dependencies import get_current_profile
from insights import compute_drift_suggestions
from models import PalateDriftSuggestion, Profile

router = APIRouter()
logger = logging.getLogger("sommelier.api")


@router.get("/profile/insights", response_model=list[PalateDriftSuggestion])
def get_insights(profile: Profile = Depends(get_current_profile)) -> list[PalateDriftSuggestion]:
    """Return palate drift suggestions based on this profile's recommendation history."""
    return compute_drift_suggestions(profile.id)
