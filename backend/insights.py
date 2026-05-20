"""Palate drift suggestion engine.

Analyses the most recent recommendation flights for a profile and surfaces
terms (grapes, regions) that Claude keeps recommending but the user hasn't
articulated as preferences.  When a term appears in ≥ _MIN_HIT_RATE of recent
flights but is absent from the profile, we emit a PalateDriftSuggestion.

No LLM calls are made — this is purely statistical analysis of saved flights.
"""

import json
import logging
import sqlite3

from cache import DB_PATH
from models import PalateDriftSuggestion
from profile import build_taste_profile_pydantic, load_profile_data

logger = logging.getLogger("sommelier.insights")

_MIN_FLIGHTS = 3       # Minimum flights before generating suggestions
_FLIGHT_WINDOW = 20    # How many recent flights to analyse
_MIN_HIT_RATE = 0.30   # Term must appear in ≥ 30 % of flights to be surfaced
_MAX_SUGGESTIONS = 3   # Cap on returned suggestions


def _load_recent_flights(profile_id: str, limit: int) -> list[tuple[str, dict]]:
    """Return (flight_id, parsed_response) for the most recent flights."""
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute(
            "SELECT id, response_json FROM flights "
            "WHERE profile_id = ? ORDER BY created_at DESC LIMIT ?",
            (profile_id, limit),
        ).fetchall()
    results: list[tuple[str, dict]] = []
    for flight_id, response_json in rows:
        try:
            results.append((flight_id, json.loads(response_json)))
        except (json.JSONDecodeError, TypeError):
            logger.warning("insights: invalid response_json for flight=%s", flight_id)
    return results


def _extract_term_flight_map(
    flights: list[tuple[str, dict]],
) -> dict[str, dict[str, set[str]]]:
    """Build {dimension: {term: {flight_id, ...}}} from raw flight data."""
    grape_flights: dict[str, set[str]] = {}
    region_flights: dict[str, set[str]] = {}

    for flight_id, response in flights:
        for rec in response.get("recommendations", []):
            if grape := (rec.get("grape") or "").strip():
                grape_flights.setdefault(grape, set()).add(flight_id)
            if region := (rec.get("region") or "").strip():
                region_flights.setdefault(region, set()).add(flight_id)

    return {
        "preferred_grapes": grape_flights,
        "preferred_regions": region_flights,
    }


def compute_drift_suggestions(profile_id: str) -> list[PalateDriftSuggestion]:
    """Return palate drift suggestions for a profile.

    Returns an empty list when there are too few flights or no pattern emerges.
    """
    flights = _load_recent_flights(profile_id, _FLIGHT_WINDOW)
    if len(flights) < _MIN_FLIGHTS:
        logger.debug("insights: %d flights < minimum %d — skipping", len(flights), _MIN_FLIGHTS)
        return []

    taste_profile = build_taste_profile_pydantic(load_profile_data(profile_id))

    # Build lowercased sets for substring matching against stated profile
    current_lower: dict[str, set[str]] = {
        "preferred_grapes": {g.lower() for g in (taste_profile.preferred_grapes or [])},
        "preferred_regions": {r.lower() for r in (taste_profile.preferred_regions or [])},
    }
    current_display: dict[str, list[str]] = {
        "preferred_grapes": list(taste_profile.preferred_grapes or []),
        "preferred_regions": list(taste_profile.preferred_regions or []),
    }

    term_map = _extract_term_flight_map(flights)
    total_flights = len(flights)
    suggestions: list[PalateDriftSuggestion] = []

    for dimension, term_flights in term_map.items():
        existing = current_lower.get(dimension, set())

        # Candidates: above threshold AND not already in profile (substring-safe check)
        candidates: list[tuple[float, str, list[str]]] = []
        for term, flight_ids in term_flights.items():
            hit_rate = len(flight_ids) / total_flights
            if hit_rate < _MIN_HIT_RATE:
                continue
            tl = term.lower()
            if any(tl in ex or ex in tl for ex in existing):
                continue  # Overlaps with an existing preference
            candidates.append((hit_rate, term, sorted(flight_ids)))

        if not candidates:
            continue

        # Surface only the single strongest signal per dimension
        candidates.sort(reverse=True)
        top_rate, top_term, supporting = candidates[0]
        flight_count = len(supporting)
        dim_label = dimension.replace("_", " ")

        suggestions.append(
            PalateDriftSuggestion(
                dimension=dimension,
                current=current_display.get(dimension, []),
                suggested=[top_term],
                rationale=(
                    f"'{top_term}' appeared in {flight_count} of your last {total_flights} "
                    f"recommendation flights but isn't in your stated {dim_label}."
                ),
                supporting_flight_ids=supporting,
            )
        )

        if len(suggestions) >= _MAX_SUGGESTIONS:
            break

    logger.info(
        "insights: profile=%s flights=%d suggestions=%d",
        profile_id,
        total_flights,
        len(suggestions),
    )
    return suggestions
