# main.py

## Responsibility

FastAPI application root. Defines all user-facing endpoints, request/response logging middleware, exception handlers, and utility functions for inventory term analysis.

## Dependencies

- `FastAPI`, `uvicorn` (web server)
- `pydantic` (response models)
- `inventory`, `cache`, `prompt`, `profile`, `models`, `parser`, `recommender`, `meal_parser`, `scorer`, `logging_utils`, `seed_profile` (internal modules)
- `routes.debug` (sub-router)

## Inputs/Outputs

**Inputs**: HTTP requests with form data (file uploads, form fields).
**Outputs**: JSON responses conforming to models.py schemas + HTTP status codes.

## Key Constants & Functions

**_MAX_UPLOAD_BYTES** = 20 * 1024 * 1024: Maximum allowed file size for uploads (20 MB). All three upload endpoints check size and raise `HTTPException(status_code=413)` if exceeded.

**_RATE_LIMIT_MAX** = 10, **_RATE_LIMIT_WINDOW** = 60: Rate limiting configuration. Allows up to 10 requests per 60-second window per client IP on `/recommend`.

**_check_rate_limit(ip: str)**: Token-bucket rate limiter. Tracks request timestamps per client IP in `_rate_counts` dict. Raises `HTTPException(status_code=429)` if limit exceeded.

**log_requests middleware**: Assign request_id, measure elapsed time, log start/end with method, path, status.

**upload_inventory**: Read file bytes, check size limit, decode CellarTracker TSV, save to inventory.json, bust cache. Return bottle count.

**upload_profile**: Read file bytes, check size limit, detect and save profile export type. Bust cache. Build Pydantic TasteProfile via `build_taste_profile_pydantic()`. Return type string + taste_profile.

**seed_profile** (`POST /seed-profile`): Accepts `SeedProfileRequest` JSON (3–7 loved + 0–3 disliked named wines). Calls `seed_profile.infer_profile_from_seeds()`, persists via `persist_seed_profile()` (which backs up the existing profile), busts cache, returns `UploadProfileResponse` with `export_type="seed_bottles"` and the populated `TasteProfile` carrying `profile_source="seed_bottles"` + `inference_confidence`.

**revert_profile** (`POST /profile/revert`): Restore `profile_data.json` from the backup created by `/seed-profile`. Returns 404 if no backup exists. Busts cache on success.

**get_inventory**: Load and return current inventory with age_hours + stale flag.

**profile_summary**: Load profile data, build taste profile, return structured response. Surfaces `profile_source`, `inference_confidence`, and `seed_bottle_count`. Skips the Anthropic enrichment call when the profile is already seed-derived (it carries its own `style_summary`). On Anthropic enrichment failures, logs specific error types (APIError, ValueError, RuntimeError, Exception) but silently falls back to None (non-fatal).

**startup sequence** (module level):
  1. `init_db()` — ensure cache table exists
  2. `purge_expired()` — evict stale cache entries; logs `cache_purge_on_startup expired_entries=N`

**recommend** (main endpoint):
  1. Check rate limit via `_check_rate_limit()` (raises 429 if exceeded). Get client IP from request object.
  2. Load inventory, compute profile hash
  3. Read wine_list bytes, check size limit (raise 413 if > 20 MB)
  4. Compute cache key from wine_list bytes, meal, inventory_hash, profile_hash
  5. Check cache; return if hit
  6. Parse wine list (dispatch by content type); compute `wine_list_hash` (MD5[:8]) and `taste_profile` (Pydantic) for scorer
  7. Try `build_enriched_profile_text()` — Anthropic call (profile enrichment). On API/ValueError/RuntimeError/Exception, log specifically and fall back to None (standard profile used in prompt)
  8. Parse meal via `parse_meal_description(meal)` → `meal_to_wine_hints()` → `meal_hints` string
  9. Build system prompt with cellar context + enriched profile + meal hints
  10. Call `get_recommendation()` from recommender.py — Anthropic call (wrapped in try/except)
  11. On success: score via `score_recommendation()`, log event via `log_recommendation_event()` (both non-blocking), cache result, return response
  12. On `HTTPException`: log error event, re-raise
  13. On bare `Exception`: log error event, raise `HTTPException(502, detail="Recommendation provider failed. Please try again.")`

**Exception handlers** (module level):
  - `http_exception_handler`: Preserves status codes for intentional HTTPExceptions (e.g. 502 from /recommend). Returns `{"detail": ...}`.
  - `unhandled_exception_handler`: Catches all other exceptions; logs with `logger.exception`; returns 500 `{"detail": "Internal server error", "error_type": ...}`.

## Patterns & Gotchas

- Request ID generation: `str(uuid.uuid4())[:8]` for brevity in logs.
- Cache key: SHA256 hash; deterministic across requests.
- CellarTracker inventory terms: extracted via `_inventory_terms_by_frequency()` (Counter-based, filters stopwords). Top 5 become `cellar_summary`, top 10 become `relevant_bottles` filter.
- `style_terms` form parameter allows user override of auto-detected terms.
- Exception handlers preserve HTTP status codes (important for `/recommend` 502 fallback).
- CORS: Allow all origins + methods (portfolio app, not sensitive to CORS restrictions).
- Profile enrichment is attempted but non-fatal: if `build_enriched_profile_text()` fails or returns < 20 chars, `enriched_profile = None` and the standard profile path is used instead. Logged as warning.
- Two Anthropic calls per recommend: enrichment (profile enrichment) + recommendation (main recommendation). Both are non-fatal on failure.
- Scoring and JSONL logging are non-blocking: if `score_recommendation()` or `log_recommendation_event()` raise, the exception is caught and logged as `scoring_and_logging_failed` but the response is still returned. Never blocks the response path.
- `wine_list_hash` is MD5[:8] of the parsed text (not the raw bytes), so it is stable across different file containers for the same wine list content.
- Backup files: `/seed-profile` creates `profile_data.backup.json` before overwriting; `/profile/revert` restores from the most recent backup.

## Known Issues / TODOs

- Image uploads: OCR text extraction is implemented (pytesseract + PIL in parser.py). Base64 image is also passed to Ollama for vision-capable models (not yet tested with a vision model).
- Cache TTL is `CACHE_TTL_HOURS = 168` in cache.py. Expired entries are purged at startup and lazily on read; no API endpoint to adjust TTL.
- Request logging includes full env (debug endpoints); be careful with secrets.

## Testing

Manual: upload TSV → upload PDF → upload meal → verify RecommendationResponse structure and caching.
