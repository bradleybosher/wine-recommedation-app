"""Flight history route: list, retrieve, and delete persisted recommendation flights."""
import json
import logging

from fastapi import APIRouter, HTTPException

from cache import delete_flight, get_flight, list_flights
from models import FlightRecord, FlightSummary, RecommendationResponse

router = APIRouter()
logger = logging.getLogger("sommelier.api")


@router.get("/history")
async def list_history(limit: int = 50, offset: int = 0) -> list[FlightSummary]:
    """List all past flights, newest first."""
    rows = list_flights(limit=limit, offset=offset)
    return [FlightSummary(**row) for row in rows]


@router.get("/history/{flight_id}")
async def get_history(flight_id: str) -> FlightRecord:
    """Retrieve a single flight by ID with full recommendation data."""
    flight = get_flight(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")

    try:
        response_data = json.loads(flight["response_json"])
        response = RecommendationResponse(**response_data)
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
    )


@router.delete("/history/{flight_id}")
async def delete_history(flight_id: str) -> dict:
    """Delete a flight by ID."""
    success = delete_flight(flight_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    return {"id": flight_id, "deleted": True}
