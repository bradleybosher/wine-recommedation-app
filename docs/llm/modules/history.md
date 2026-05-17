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

**PATCH /history/{flight_id}/feedback** → `{"ok": true}`
  - Body: `FlightFeedback` JSON (`chip`, `recordedAt`)
  - Merges feedback into the flight's `response_json` blob via `cache.update_flight_feedback()`
  - 404 if not found

**DELETE /history/{flight_id}** → `{"id": str, "deleted": true}`
  - 404 if not found

## Dependencies

- `cache`: `list_flights`, `get_flight`, `delete_flight`, `update_flight_feedback`
- `models`: `FlightFeedback`, `FlightSummary`, `FlightRecord`, `RecommendationResponse`

## Patterns & Gotchas

- **No write path here (except feedback)**: Flights are auto-saved inside `routes/recommend.py` (best-effort, non-fatal). Feedback is written via `PATCH /history/{id}/feedback`.
- **Re-hydration contract**: `FlightRecord.response` is a full `RecommendationResponse`. The frontend drops it directly into `setRecommendations()` and navigates to `/flight`, giving full drill-down to `/detail` and `/compare`.
- **Feedback storage**: Feedback is stored inside `response_json` at key `"feedback"`, not in a separate column. `get_history` pops this key before building `RecommendationResponse`, then constructs `FlightFeedback` separately and attaches it to `FlightRecord.feedback`.
- **source_mode / occasion / menu**: Stored as raw form field values from the original request; may be empty strings for legacy flights.
