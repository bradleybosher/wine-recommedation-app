# routes/recommend.py

## Responsibility

The `POST /recommend` endpoint — the app's primary workflow. Wine list upload + meal context → top-3 recommendations.

## Endpoint

**`POST /recommend`** → `RecommendationResponse`
Form fields: `wine_list: UploadFile`, `meal: str`, `style_terms: str = ""`.

Pipeline:

1. `rate_limit.check_rate_limit(client_ip)` — 429 if exceeded.
2. Load inventory + compute profile hash (`md5` of sorted JSON).
3. Read `wine_list` bytes; 413 if over `MAX_UPLOAD_BYTES`.
4. Build cache key from bytes + meal + inventory hash + profile hash; return cached response if present and valid.
5. Parse wine list — first try `cache.get_parse_cached(parse_key)`, otherwise call `parser.parse_wine_list(...)`. On `parser.OCRError` raise 422.
6. Strip invisible Unicode (module-level `_INVISIBLE_RE`), trim blanks, filter via `inventory.filter_wine_list(text, taste_profile)`.
7. Try `profile.build_enriched_profile_text(ANTHROPIC_API_KEY, ANTHROPIC_MODEL)` — Anthropic call. APIError / ValueError / RuntimeError / Exception each logged distinctly; on failure or short output (< 20 chars) fall back to the standard profile.
8. Compute `cellar_summary` (top 5 terms) and `relevant` bottles (top 10 terms, possibly overridden by `style_terms`) via `cellar_terms.*` + `inventory.get_relevant_bottles`.
9. `meal_parser.parse_meal_description(meal)` → `meal_to_wine_hints`.
10. `prompt.build_system_prompt(...)` with cellar summary, enriched profile, meal hints, profile source.
11. `recommender.get_recommendation(...)` — main Anthropic call.
12. On success: `scorer.score_recommendation` (capping confidence to `medium` for seed-derived profiles) and `logging_utils.log_recommendation_event`; both wrapped in try/except — scoring/logging failures never block the response. Cache the result and return.
13. On `HTTPException`: log error event, re-raise.
14. On any other `Exception`: log error event, raise 502 `"Recommendation provider failed. Please try again."`.

## Dependencies

- `bootstrap.ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `MAX_UPLOAD_BYTES`
- `cache.{get_cached, get_parse_cached, inventory_hash, make_key, make_parse_key, set_cached, set_parse_cached}`
- `cellar_terms.cellar_character_from_terms`, `inventory_terms_by_frequency`
- `inventory.{filter_wine_list, get_relevant_bottles, load_inventory}`
- `logging_utils.log_recommendation_event`
- `meal_parser.{meal_to_wine_hints, parse_meal_description}`
- `models.RecommendationResponse`
- `parser.{OCRError, parse_wine_list}` — both hoisted to top-level imports (no in-function imports)
- `profile.{build_enriched_profile_text, build_taste_profile_pydantic, extract_profile_preference_terms, load_profile_data}`
- `prompt.build_system_prompt`
- `rate_limit.check_rate_limit`
- `recommender.get_recommendation`
- `scorer.score_recommendation`

## Patterns & Gotchas

- `_INVISIBLE_RE` is compiled once at module load (was previously re-compiled per request inside the handler).
- The parse cache is keyed by file bytes alone, so the same uploaded list reuses extracted text across different meals / profiles.
- Two Anthropic calls per request (profile enrichment + recommendation). Only the second is fatal on failure.
- `wine_list_hash` is `md5(parsed_text)[:8]` — stable across container formats for the same wine-list content.
