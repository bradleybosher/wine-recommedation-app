# test_fixtures.py

## Responsibility

Canned `RecommendationResponse` objects used by `/recommend` when `bootstrap.TEST_MODE` is enabled. Lets the frontend UX be iterated on without burning Anthropic credits.

## Public surface

- `FIXTURES: dict[str, RecommendationResponse]` — keys are fixture names:
  - `happy` — three well-formed wines, full `fitMarkers`, mixed high/medium confidence, `listQualityNote=None`.
  - `sparse` — wines with most optional fields (`producer`, `vintage`, `region`, `price`, `fitMarkers`) `None`/empty to exercise fallback rendering. `listQualityNote` populated.
  - `long_reasoning` — multi-sentence `reasoning` per wine plus a long `profile_match_summary` for text-wrapping/truncation testing.
  - `low_confidence` — every wine's `confidence` starts `"low — ..."` and `listQualityNote` is populated (poor-list scenario).
  - `two_wines` — only two entries in `recommendations` to verify the UI when fewer than three results are returned.

## Patterns & Gotchas

- Fixtures are constructed from `models.RecommendationResponse` / `WineRecommendation` Pydantic models, so any schema drift fails at backend import — not at request time.
- Only consumed by `routes/recommend.py` and only when `TEST_MODE` is true.
- Add new variants by extending the dict; no other code changes needed.
