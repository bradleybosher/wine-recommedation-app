# routes/recommend.py

## Responsibility

The `POST /recommend` endpoint — the app's primary workflow. Wine list upload + meal context → top-N recommendations (default 3).

## Endpoint

**`POST /recommend`** → `RecommendationResponse`

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
4. Load inventory + compute profile hash (`md5` of sorted JSON).
5. Read `wine_list` bytes (when `use_wine_list`); 413 if over `MAX_UPLOAD_BYTES`.
6. Build cache key from bytes + `effective_meal|bottle_count|ceiling` + inventory hash + profile hash; return cached response if present and valid.
7. **Wine list parsing** (when `use_wine_list` only):
   - Try `cache.get_parse_cached(parse_key)`, otherwise call `parser.parse_wine_list(...)`. On `parser.OCRError` raise 422.
   - Strip invisible Unicode (`_INVISIBLE_RE`), trim blanks, filter via `inventory.filter_wine_list(text, taste_profile)`.
8. **Enriched profile**: Try `profile.build_enriched_profile_text(...)`. On any error fall back to standard profile (non-fatal).
9. Compute `cellar_summary` (top 5 terms) and `relevant` bottles (top 10 terms, possibly overridden by `effective_style`) via `cellar_terms.*` + `inventory.get_relevant_bottles`.
10. `meal_parser.parse_meal_description(effective_meal)` → `meal_to_wine_hints`.
11. `prompt.build_system_prompt(...)` with cellar summary, enriched profile, meal hints, profile source, `bottle_count`, `budget_ceiling=ceiling`. Also passes `taste_markers` and `palate_persona` extracted from `build_taste_profile(load_profile_data())` so the prompt can render the numeric markers block and quote the persona verbatim (both populated by `_synthesized` or `_inferred` profiles; absent for legacy CT-only).
12. `recommender.get_recommendation(wine_list_text, effective_meal, ...)` — main Anthropic call.
13. On success: `scorer.score_recommendation` (capping confidence to `medium` for seed-derived profiles) and `logging_utils.log_recommendation_event`; both wrapped in try/except — scoring/logging failures never block the response. Cache the result and return.
14. On `HTTPException`: log error event, re-raise.
15. On any other `Exception`: log error event, raise 502 `"Recommendation provider failed. Please try again."`.

## Dependencies

- `bootstrap.ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `MAX_UPLOAD_BYTES`, `TEST_MODE`
- `test_fixtures.FIXTURES` — canned `RecommendationResponse` map used in test mode
- `cache.{get_cached, get_parse_cached, inventory_hash, make_key, make_parse_key, set_cached, set_parse_cached}`
- `cellar_terms.cellar_character_from_terms`, `inventory_terms_by_frequency`
- `inventory.{filter_wine_list, get_relevant_bottles, load_inventory}`
- `logging_utils.log_recommendation_event`
- `meal_parser.{meal_to_wine_hints, parse_meal_description}`
- `models.RecommendationResponse`
- `parser.{OCRError, parse_wine_list}`
- `profile.{build_enriched_profile_text, build_taste_profile, build_taste_profile_pydantic, extract_profile_preference_terms, load_profile_data}`
- `prompt.build_system_prompt`
- `rate_limit.check_rate_limit`
- `recommender.get_recommendation`
- `scorer.score_recommendation`

## Patterns & Gotchas

- `_INVISIBLE_RE` is compiled once at module load (not per request).
- The parse cache is keyed by file bytes alone — same uploaded list reuses extracted text across different meals/profiles.
- Cache key includes `bottle_count` and `ceiling` (via the `cache_discriminator` string) so different constraint combinations get separate cache entries.
- Two Anthropic calls per request (profile enrichment + recommendation). Only the second is fatal on failure.
- `wine_list_hash` is `md5(parsed_text)[:8]` — stable across container formats for the same wine-list content. Set to `"no-list"` when `source_mode="cellar"`.
- When `source_mode="cellar"`, `wine_list_text` is empty string and `get_recommendation` receives no list — Claude recommends from profile knowledge alone.
