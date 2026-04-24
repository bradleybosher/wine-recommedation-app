# main.py

## Responsibility

FastAPI application root. Defines all user-facing endpoints, request/response logging middleware, exception handlers, and utility functions for inventory term analysis.

## Dependencies

- `FastAPI`, `uvicorn` (web server)
- `pydantic` (response models)
<<<<<<< HEAD
- `inventory`, `cache`, `prompt`, `profile`, `models`, `parser`, `recommender`, `meal_parser`, `scorer`, `logging_utils` (internal modules)
=======
- `inventory`, `cache`, `prompt`, `profile`, `models`, `parser`, `recommender`, `meal_parser` (internal modules)
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
- `routes.debug` (sub-router)

## Inputs/Outputs

**Inputs**: HTTP requests with form data (file uploads, form fields).
**Outputs**: JSON responses conforming to models.py schemas + HTTP status codes.

## Key Functions

**log_requests middleware**: Assign request_id, measure elapsed time, log start/end with method, path, status.

**upload_inventory**: Decode CellarTracker TSV, save to inventory.json, bust cache. Return bottle count.

**upload_profile**: Detect and save profile export type. Bust cache. Build Pydantic TasteProfile via `build_taste_profile_pydantic()`. Return type string + taste_profile.

**get_inventory**: Load and return current inventory with age_hours + stale flag.

**profile_summary**: Load profile data, build taste profile, return structured response.

**startup sequence** (module level):
  1. `init_db()` — ensure cache table exists
  2. `purge_expired()` — evict stale cache entries; logs `cache_purge_on_startup expired_entries=N`

**recommend** (main endpoint):
  1. Load inventory, compute profile hash
  2. Compute cache key from wine_list bytes, meal, inventory_hash, profile_hash
  3. Check cache; return if hit
<<<<<<< HEAD
  4. Parse wine list (dispatch by content type); compute `wine_list_hash` (MD5[:8]) and `taste_profile` (Pydantic) for scorer
  5. Try `build_enriched_profile_text(OLLAMA_URL, OLLAMA_MODEL)` — first Ollama call (profile enrichment). On failure or empty result, fall back to None (standard profile used in prompt)
  6. Parse meal via `parse_meal_description(meal)` → `meal_to_wine_hints()` → `meal_hints` string
  7. Build system prompt with cellar context + enriched profile + meal hints
  8. Call `get_recommendation()` from recommender.py — second Ollama call (wrapped in try/except)
  9. On success: score via `score_recommendation()`, log event via `log_recommendation_event()` (both non-blocking), cache result, return response
  10. On `HTTPException`: log error event, re-raise
  11. On bare `Exception`: log error event, raise `HTTPException(502)`
=======
  4. Parse wine list (dispatch by content type)
  5. Try `build_enriched_profile_text(OLLAMA_URL, OLLAMA_MODEL)` — first Ollama call (profile enrichment). On failure or empty result, fall back to None (standard profile used in prompt)
  6. Parse meal via `parse_meal_description(meal)` → `meal_to_wine_hints()` → `meal_hints` string
  7. Build system prompt with cellar context + enriched profile + meal hints
  8. Call `get_recommendation()` from recommender.py — second Ollama call
  9. Cache result, return response
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)

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
- Two Ollama calls per recommend: enrichment (30s timeout in profile.py) + recommendation (120s timeout in recommender.py). Total max ≈ 6+ minutes on bad hardware.
<<<<<<< HEAD
- Scoring and JSONL logging are non-blocking: if `score_recommendation()` or `log_recommendation_event()` raise, the exception is caught and logged as `scoring_and_logging_failed` but the response is still returned. Never blocks the response path.
- `wine_list_hash` is MD5[:8] of the parsed text (not the raw bytes), so it is stable across different file containers for the same wine list content.
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)

## Known Issues / TODOs

- Image uploads: OCR text extraction is implemented (pytesseract + PIL in parser.py). Base64 image is also passed to Ollama for vision-capable models (not yet tested with a vision model).
- Cache TTL is `CACHE_TTL_HOURS = 168` in cache.py. Expired entries are purged at startup and lazily on read; no API endpoint to adjust TTL.
- Request logging includes full env (debug endpoints); be careful with secrets.

## Testing

Manual: upload TSV → upload PDF → upload meal → verify RecommendationResponse structure and caching.
