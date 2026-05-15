# routes/history.py

## Responsibility

HTTP endpoints for browsing and retrieving persisted recommendation flights. Reads from the `flights` table in `cellar.db` (written by `routes/recommend.py` on every successful recommendation). Does not trigger LLM calls.

## Endpoints

**GET /history** → `list[FlightSummary]`
  - Query params: `limit` (default 50), `offset` (default 0)
  - Returns lightweight summaries sorted newest-first
  - Calls `cache.list_flights()`

**GET /history/{flight_id}** → `FlightRecord`
  - Fetches full flight by UUID hex id
  - Deserialises `response_json` → `RecommendationResponse` and wraps in `FlightRecord`
  - 404 if not found; 500 if deserialisation fails

**DELETE /history/{flight_id}** → `{"id": str, "deleted": true}`
  - 404 if not found

## Dependencies

- `cache`: `list_flights`, `get_flight`, `delete_flight`
- `models`: `FlightSummary`, `FlightRecord`, `RecommendationResponse`

## Patterns & Gotchas

- **No write path here**: Flights are auto-saved inside `routes/recommend.py` (best-effort, non-fatal). This module is read/delete only.
- **Re-hydration contract**: `FlightRecord.response` is a full `RecommendationResponse`. The frontend drops it directly into `setRecommendations()` and navigates to `/flight`, giving full drill-down to `/detail` and `/compare`.
- **source_mode / occasion / menu**: Stored as raw form field values from the original request; may be empty strings for legacy flights.
