# routes/history.py

## Responsibility

HTTP endpoints for browsing and retrieving persisted recommendation flights. Reads from the `flights` table in `cellar.db` (written by `routes/recommend.py` on every successful recommendation). All endpoints require Bearer JWT + `X-Profile-Id` header and filter/scope results to the active profile. Does not trigger LLM calls.

## Authentication

All endpoints in this module require:
- **Bearer JWT** in the `Authorization` header (JWT token issued at registration/login)
- **`X-Profile-Id`** header specifying the active profile UUID

Per-request flow: `Depends(get_current_profile)` extracts the user_id from the JWT and loads the profile by ID. The profile object is then passed to each endpoint handler. All flight operations are scoped to the active profile.

## Endpoints

**GET /history** → `list[FlightSummary]`
  - Requires Bearer JWT + `X-Profile-Id` header.
  - Query params: `limit` (default 50), `offset` (default 0)
  - Returns lightweight summaries sorted newest-first, filtered by `profile.id`
  - Calls `cache.list_flights(profile_id=profile.id)`

**GET /history/{flight_id}** → `FlightRecord`
  - Requires Bearer JWT + `X-Profile-Id` header.
  - Fetches full flight by UUID hex id via `cache.get_flight(flight_id)` (404 if absent)
  - Enforces ownership via `_enforce_flight_ownership(flight, profile)` — returns 404 if the flight belongs to a different profile (prevents confirming the existence of flights outside the user's account)
  - Deserialises `response_json` → `RecommendationResponse` and wraps in `FlightRecord`
  - 404 if not found or not owned; 500 if deserialisation fails

**PATCH /history/{flight_id}/feedback** → `{"ok": true}`
  - Requires Bearer JWT + `X-Profile-Id` header.
  - Body: `FlightFeedback` JSON (`chip`, `recordedAt`)
  - Fetches the flight via `cache.get_flight(flight_id)` (404 if absent), then enforces ownership via `_enforce_flight_ownership(flight, profile)`
  - Merges feedback into the flight's `response_json` blob via `cache.update_flight_feedback(flight_id, body)`
  - 404 if not found or not owned

**DELETE /history/{flight_id}** → `{"id": str, "deleted": true}`
  - Requires Bearer JWT + `X-Profile-Id` header.
  - Fetches the flight via `cache.get_flight(flight_id)` (404 if absent), then enforces ownership via `_enforce_flight_ownership(flight, profile)`
  - 404 if not found or not owned

## Helpers

- **`_enforce_flight_ownership(flight: dict, profile: Profile)`** — module-private. Receives an already-fetched flight dict and the active `Profile` object; it does **not** fetch the flight itself (each caller fetches via `cache.get_flight(flight_id)` first and 404s on absence). Asserts the flight's `profile_id` matches `profile.id`; raises 404 `HTTPException` otherwise. Used by all single-flight endpoints to prevent information leakage (confirming the existence of flights outside the user's account).

## Dependencies

- `cache`: `list_flights`, `get_flight`, `delete_flight`, `update_flight_feedback`
- `models`: `FlightFeedback`, `FlightSummary`, `FlightRecord`, `Profile`, `RecommendationResponse`
- `dependencies.get_current_profile` — dependency injector for authenticated profile resolution

## Patterns & Gotchas

- **No write path here (except feedback)**: Flights are auto-saved inside `routes/recommend.py` (best-effort, non-fatal). Feedback is written via `PATCH /history/{id}/feedback`.
- **Re-hydration contract**: `FlightRecord.response` is a full `RecommendationResponse`. The frontend drops it directly into `setRecommendations()` and navigates to `/flight`, giving full drill-down to `/detail` and `/compare`.
- **Feedback storage**: Feedback is stored inside `response_json` at key `"feedback"`, not in a separate column. `get_history` pops this key before building `RecommendationResponse`, then constructs `FlightFeedback` separately and attaches it to `FlightRecord.feedback`.
- **source_mode / occasion / menu**: Stored as raw form field values from the original request; may be empty strings for legacy flights.
- **Ownership enforcement**: Returning 404 on ownership mismatch (rather than 403 Forbidden) prevents confirming the existence of a flight ID to an unauthorized user. All single-flight endpoints use `_enforce_flight_ownership` before processing.
