# routes/recommend.py

## Responsibility

The `POST /recommend` endpoint — the app's primary workflow. Wine list upload + meal context → top-N recommendations (default 3).

## Authentication

The endpoint requires:
- **Bearer JWT** in the `Authorization` header (JWT token issued at registration/login)
- **`X-Profile-Id`** header specifying the active profile UUID

Per-request flow: `Depends(get_current_profile)` extracts the user_id from the JWT and loads the profile by ID. The profile object is then passed to the endpoint handler.

## Endpoint

**`POST /recommend`** → `RecommendationResponse`

Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`.

### Form Fields

Legacy fields (kept for backward compatibility during frontend cutover):
- `meal: str = ""` — free-text meal description
- `style_terms: str = ""` — comma-separated cellar style override terms

New Preferences fields (Phase 5):
- `occasion: str = ""` — dining context (e.g., "business dinner", "anniversary")
- `menu: str = ""` — dish description for the evening
- `cellar_leans: str = ""` — style direction from the user's cellar character
- `temperament: str = ""` — mood/style temperament (e.g., "bold", "elegant")
- `ceiling: str = ""` — budget ceiling per bottle (e.g., "$150")
- `bottle_count: int = 3` — number of recommendations to return
- `source_mode: str = "winelist"` — `"winelist"` (default) or `"cellar"` (skip wine list parsing)

File/test:
- `wine_list: UploadFile = None` — wine list PDF/image; optional when `source_mode="cellar"`
- `test_fixture: str = ""` — fixture name when `TEST_MODE` active

### Effective Meal / Style Composition

- `effective_meal = f"{occasion} {menu}".strip()` if either is set; otherwise falls back to legacy `meal`
- `effective_style = f"{cellar_leans} {temperament}".strip()` if either is set; otherwise falls back to legacy `style_terms`

## Pipeline

1. `rate_limit.check_rate_limit(client_ip)` — 429 if exceeded.
2. **Test-mode short-circuit:** if `bootstrap.TEST_MODE` is true and `test_fixture` is non-empty, drain the upload (if present), look up `test_fixtures.FIXTURES[test_fixture]`, and return it directly. Unknown fixture name → 400 with the list of valid names.
3. Determine `use_wine_list = source_mode != "cellar" and wine_list is not None`. If `source_mode != "cellar"` and no file uploaded → 422.
4. Load inventory via `inventory.load_inventory(profile.id)` + compute profile hash (`md5` of sorted JSON).
5. Read `wine_list` bytes (when `use_wine_list`); 413 if over `MAX_UPLOAD_BYTES`.
6. Build cache key from bytes + `effective_meal|bottle_count|ceiling` + inventory hash + profile hash; return cached response if present and valid.
7. **Wine list parsing** (when `use_wine_list` only):
   - Try `cache.get_parse_cached(parse_key)`, otherwise call `parser.parse_wine_list(...)`. On `parser.OCRError` raise 422.
   - Strip invisible Unicode (`_INVISIBLE_RE`), trim blanks, filter via `inventory.filter_wine_list(text, taste_profile)`.
   - **Retrieval ranking**: call `retrieval.rank_wine_list(text, taste_profile, override_terms=override_terms, limit=40)`. No-op for short lists (≤ 40 lines). Scores each line by profile-signal overlap and keeps the top 40 — caps token use for large menus without an extra API call.
8. **Enriched profile**: Try `profile.build_enriched_profile_text(profile.id, ...)`. On any error fall back to standard profile (non-fatal).
9. Compute `cellar_summary` (top 5 terms) and `relevant` bottles (top 10 terms, possibly overridden by `effective_style`) via `cellar_terms.*` + `inventory.get_relevant_bottles`.
10. `meal_parser.parse_meal_description(effective_meal)` → `meal_to_wine_hints`.
11. **Tasting note library + aspirational skew**: reads `consumed_rows` from `profile_data_raw`. Calls `_build_tasting_note_library(consumed_rows)` to build a formatted `**TASTING NOTE LIBRARY**` block (top-scored + bottom-scored notes, deduplicated by varietal/region, max 15 entries). Calls `palate_stats.compute_palate_stats(consumed_rows, inventory_rows=bottles)` to extract `aspirational_skew.summary_line`. Both are passed to `build_system_prompt()` and are empty strings when no consumed rows are present.
12. `prompt.build_system_prompt(...)` with cellar summary, enriched profile, meal hints, profile source, `bottle_count`, `budget_ceiling=ceiling`, `taste_markers`, `palate_persona`, `source_mode`, `tasting_note_library`, `aspirational_skew`.
12. `recommender.get_recommendation(wine_list_text, effective_meal, ...)` — main Anthropic call.
13. **Per-wine grounding** (winelist mode only): after recommendations are returned, iterate and set `rec.verified_on_list = scorer._is_grounded(rec.wine_name, wine_list_text)` on each wine.
14. On success: `scorer.score_recommendation` (capping confidence to `medium` for seed-derived profiles) and `logging_utils.log_recommendation_event`; both wrapped in try/except — scoring/logging failures never block the response.
15. `save_flight(profile_id=profile.id, ...)` — best-effort; captures the returned `flight_id` and scopes the flight record to the active profile. Result cached **before** attaching `flight_id` (so cache hits don't replay a stale id); then `recommendation.flight_id = flight_id` is set and response returned.
16. On `HTTPException`: log error event, re-raise.
17. On any other `Exception`: log error event, raise 502 `"Recommendation provider failed. Please try again."`.

## Module-Level Helpers

### `_build_tasting_note_library(consumed_rows, max_entries=15) → str`

Extracts tasting notes from CellarTracker consumed rows and formats them as a prompt-ready library block.

- Skips rows with no `ConsumptionNote`.
- Extracts score from `CScore` or `PScore` (first present wins).
- Deduplicates by `varietal|region` key — one note per varietal+region pair.
- Orders by descending score, then unscored. Takes top-scored entries (2/3 of `max_entries`) and up to 4 bottom-scored entries.
- Each line: `- {Producer} {Wine} [{score}pts]: "{note[:150]}…"`
- Returns a `**TASTING NOTE LIBRARY** (direct quotes…):\n…` block, or empty string if no notes.

## Dependencies

- `bootstrap.ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `MAX_UPLOAD_BYTES`, `TEST_MODE`
- `test_fixtures.FIXTURES` — canned `RecommendationResponse` map used in test mode
- `cache.{get_cached, get_parse_cached, inventory_hash, make_key, make_parse_key, set_cached, set_parse_cached, save_flight}`
- `cellar_terms.cellar_character_from_terms`, `inventory_terms_by_frequency`
- `inventory.{filter_wine_list, get_relevant_bottles, load_inventory}`
- `logging_utils.log_recommendation_event`
- `meal_parser.{meal_to_wine_hints, parse_meal_description}`
- `models.RecommendationResponse`
- `palate_stats.compute_palate_stats` — statistical palate analysis for aspirational skew
- `parser.{OCRError, parse_wine_list}`
- `retrieval.rank_wine_list`
- `profile.{build_enriched_profile_text, build_taste_profile, build_taste_profile_pydantic, extract_profile_preference_terms, load_profile_data}`
- `prompt.build_system_prompt`
- `rate_limit.check_rate_limit`
- `recommender.get_recommendation`
- `routes.auth.get_current_profile` — dependency injector for authenticated profile resolution
- `scorer._is_grounded`, `scorer.score_recommendation`

## Patterns & Gotchas

- `_INVISIBLE_RE` is compiled once at module load (not per request).
- The parse cache is keyed by file bytes alone — same uploaded list reuses extracted text across different meals/profiles.
- Cache key includes `bottle_count` and `ceiling` (via the `cache_discriminator` string) so different constraint combinations get separate cache entries.
- Two Anthropic calls per request (profile enrichment + recommendation). Only the second is fatal on failure.
- `wine_list_hash` is `md5(parsed_text)[:8]` — stable across container formats for the same wine-list content. Set to `"no-list"` when `source_mode="cellar"`.
- When `source_mode="cellar"`, `wine_list_text` is empty string and `get_recommendation` receives no list — Claude recommends from profile knowledge alone.
