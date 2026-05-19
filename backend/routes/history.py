"""Flight history route: list, retrieve, and delete persisted recommendation flights."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from cache import delete_flight, get_flight, list_flights, update_flight_feedback
from dependencies import get_current_profile
from models import FlightFeedback, FlightRecord, FlightSummary, Profile, RecommendationResponse

router = APIRouter()
logger = logging.getLogger("sommelier.api")


def _enforce_flight_ownership(flight: dict, profile: Profile) -> None:
    if flight.get("profile_id") != profile.id:
        raise HTTPException(status_code=404, detail=f"Flight {flight['id']} not found")


@router.get("/history")
async def list_history(
    limit: int = 50,
    offset: int = 0,
    profile: Profile = Depends(get_current_profile),
) -> list[FlightSummary]:
    """List past flights for the active profile, newest first."""
    rows = list_flights(profile_id=profile.id, limit=limit, offset=offset)
    return [FlightSummary(**row) for row in rows]


@router.get("/history/{flight_id}")
async def get_history(
    flight_id: str,
    profile: Profile = Depends(get_current_profile),
) -> FlightRecord:
    """Retrieve a single flight by ID for the active profile with full recommendation data."""
    flight = get_flight(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    _enforce_flight_ownership(flight, profile)

    try:
        blob = json.loads(flight["response_json"])
        feedback_data = blob.pop("feedback", None)
        response = RecommendationResponse(**blob)
        feedback = FlightFeedback(**feedback_data) if feedback_data else None
    except (json.JSONDecodeError, ValueError) as exc:
        logger.exception("flight_deserialize_failed flight_id=%s: %s", flight_id, exc)
        raise HTTPException(status_code=500, detail="Failed to deserialize flight data") from exc

    return FlightRecord(
        id=flight["id"],
        created_at=flight["created_at"],
        occasion=flight["occasion"] or "",
        menu=flight["menu"] or "",
        source_mode=flight["source_mode"] or "winelist",
        bottle_count=flight["bottle_count"],
        response=response,
        feedback=feedback,
    )


@router.patch("/history/{flight_id}/feedback")
async def patch_feedback(
    flight_id: str,
    body: FlightFeedback,
    profile: Profile = Depends(get_current_profile),
) -> dict:
    """Record a one-tap feedback chip for a saved flight."""
    flight = get_flight(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    _enforce_flight_ownership(flight, profile)
    updated = update_flight_feedback(flight_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    return {"ok": True}


@router.delete("/history/{flight_id}")
async def delete_history(
    flight_id: str,
    profile: Profile = Depends(get_current_profile),
) -> dict:
    """Delete a flight by ID, scoped to the active profile."""
    flight = get_flight(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    _enforce_flight_ownership(flight, profile)
    success = delete_flight(flight_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    return {"id": flight_id, "deleted": True}
