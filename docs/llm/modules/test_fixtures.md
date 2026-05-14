# test_fixtures.py

## Responsibility

Canned `RecommendationResponse` objects used by `/recommend` when `bootstrap.TEST_MODE` is enabled. Lets the frontend UX be iterated on without burning Anthropic credits.

## Public surface

- `FIXTURES: dict[str, RecommendationResponse]` — keys are fixture names:
  - `happy` — three well-formed wines, full `fits`, mixed high/medium confidence, `listQualityNote=None`.
  - `sparse` — wines with most optional fields (`producer`, `vintage`, `region`, `price`, `fits`) `None`/empty to exercise fallback rendering. `listQualityNote` populated.
  - `long_reasoning` — multi-sentence `reasoning` per wine plus a long `profile_match_summary` for text-wrapping/truncation testing.
  - `low_confidence` — every wine's `confidence` starts `"low — ..."` and `listQualityNote` is populated (poor-list scenario).
  - `two_wines` — only two entries in `recommendations` to verify the UI when fewer than three results are returned.

## Phase 5 Enrichment Fields

All fixtures include the full set of Phase 5 enrichment fields on every `WineRecommendation`:
- `appellation`, `country`, `coords` (Coords), `grape`, `abv`
- `drink` (DrinkWindow — Python constructor uses `from_year=`, JSON serializes as `"from"`)
- `color` (WineColor — four module-level palette constants reused across fixtures)
- `bars` (StructureBars), `wheel` (dict), `nose`, `palate`, `pairs`, `critic` (Critic)

Module-level palette constants:
- `_BRUNELLO_COLOR`, `_BAROLO_COLOR`, `_CHABLIS_COLOR`, `_RHONE_COLOR`

The `sparse` fixture intentionally leaves most enrichment fields `None` to exercise frontend fallback rendering paths.

## Patterns & Gotchas

- Fixtures are constructed from `models.RecommendationResponse` / `WineRecommendation` and all nested models, so any schema drift fails at backend import — not at request time.
- Only consumed by `routes/recommend.py` and only when `TEST_MODE` is true.
- Add new variants by extending the dict; no other code changes needed.
- `fits` (not `fitMarkers`) — renamed in Phase 5.
- `DrinkWindow` uses `from_year=` in Python constructors (reserved keyword workaround).
