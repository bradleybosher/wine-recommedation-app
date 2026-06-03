# logging_utils.py

## Responsibility

Structured JSONL telemetry logger for recommendation attempts. Appends one JSON object per line to `backend/logs/recommendations.jsonl`, capturing the meal, profile/wine-list hashes, the recommended wines, and the scoring result (or an error). Distinct from `logging_setup.py`, which configures generic app logging.

## Public surface

- `log_recommendation_event(meal: str, profile_hash: str, response: Optional[RecommendationResponse], scoring_result: Optional[ScoringResult], wine_list_hash: str, error: Optional[str] = None) -> None` — Append one JSONL line describing a recommendation attempt. On success, `response` and `scoring_result` are populated; on failure they are `None` and `error` carries the message. **Never raises to the caller** — any internal failure is swallowed and reported via the meta fallback logger.

### Logged event shape

Each line is a JSON object with keys:
- `timestamp` — UTC ISO-8601 (`datetime.now(timezone.utc).isoformat()`)
- `meal` — the user's meal description
- `profile_hash` — MD5 hex of the serialised profile_data (from `main.py`)
- `wine_list_hash` — 8-char MD5 hex of the parsed wine list text
- `wine_count` — number of recommended wines
- `wines` — list of `{rank, name, confidence, price}` per recommendation
- `score` — `scoring_result.total` (or `None`)
- `score_breakdown` — `scoring_result.breakdown` (or `None`)
- `error` — error message string when the attempt failed, else `None`

## Constants / internals

- `_logger` — singleton `logging.getLogger("sommelier.recommendations")`. Attaches a `RotatingFileHandler` on `logs/recommendations.jsonl` (1 MB max, 2 backups, utf-8) with a raw `%(message)s` formatter (no decoration — pure JSON lines), level `INFO`, and `propagate = False` so events do **not** bubble up to the parent `sommelier` tree / `api.log`.
- `_fallback` — `logging.getLogger("sommelier.recommendations.meta")`. Receives `.exception(...)` calls if `log_recommendation_event` itself raises; this one **does** propagate to the sommelier tree.
- `_log_dir` — `backend/logs`, created with `mkdir(parents=True, exist_ok=True)` at import time.

## Dependencies

- `json`, `logging`, `logging.handlers`, `datetime` (standard library)
- `pathlib.Path` (log directory location)
- `models.RecommendationResponse`
- `scorer.ScoringResult`

## Patterns & Gotchas

- **Fire-and-forget**: callers do not handle exceptions from this function — it is wrapped in a `try/except` that routes failures to `_fallback`. Telemetry must never break a recommendation.
- **Non-propagating**: `propagate = False` keeps recommendation events out of `api.log`; they live solely in `recommendations.jsonl`.
- **`json.dumps(..., default=str)`**: non-serialisable values are coerced via `str`, so the call never throws on an odd type.

## Testing

1. Call with a populated `response` + `scoring_result`; assert one well-formed JSON line is appended with the expected keys.
2. Call with `response=None, scoring_result=None, error="boom"`; assert `wine_count == 0`, `wines == []`, and `error == "boom"`.
3. Force an internal serialisation failure; assert no exception propagates and `_fallback` records it.
