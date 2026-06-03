# scorer.py

## Responsibility

Pure, never-raising recommendation-quality scoring engine. Scores a
`RecommendationResponse` across four weighted dimensions and returns a single
composite float in `[0.0, 1.0]` plus a per-dimension breakdown and any
warnings. No side effects, no API calls, no I/O. Any internal error or missing
data resolves to a neutral fallback rather than propagating — the caller (e.g.
the recommend route / telemetry) is never affected by scoring failures.

## Dependencies

- `models.RecommendationResponse`, `models.TasteProfile`
- `re`, `dataclasses`, `typing`

## Public surface

```python
def score_recommendation(
    response: RecommendationResponse,
    wine_list_text: str,
    profile: Optional[TasteProfile] = None,
    cap_confidence: bool = False,
) -> ScoringResult
```

- `response` — the `RecommendationResponse` from `get_recommendation()`.
- `wine_list_text` — parsed restaurant wine-list text (used for grounding).
- `profile` — user's `TasteProfile`; may be `None` (budget_fit falls back to neutral).
- `cap_confidence` — when `True`, downgrades per-wine `"high"` confidence to
  `"medium"` before scoring (used for seed-derived / directional profiles whose
  per-wine certainty cannot exceed the profile's own certainty).

Returns a `ScoringResult`. **Never raises** — wrapped in a `try/except` that
returns an all-`0.5` neutral result on any unexpected error.

### `ScoringResult` (dataclass)

```python
@dataclass
class ScoringResult:
    total: float                 # composite in [0.0, 1.0], rounded to 4dp
    breakdown: Dict[str, float]  # per-dimension scores, each rounded to 4dp
    warnings: list[str]          # data-gap notes (e.g. empty wine_list_text)
```

`breakdown` keys: `confidence`, `completeness`, `grounding`, `budget_fit`.

## Dimensions & Weights

`total = Σ (weight × dimension_score)`:

| Dimension | Weight | What it measures |
|---|---|---|
| `confidence` | 0.30 | Mean of per-wine confidence mapped via `_CONFIDENCE_MAP` (`high`=1.00, `medium`=0.67, `low`=0.33). 0.0 if no recs. `cap_confidence` downgrades `high`→`medium` first. |
| `completeness` | 0.20 | `min(len(recommendations) / _TARGET_RECS, 1.0)` where `_TARGET_RECS = 3`. |
| `grounding` | 0.30 | Fraction of recommended wines plausibly present in `wine_list_text`. 0.0 if no recs; 0.5 (neutral) if `wine_list_text` is empty. |
| `budget_fit` | 0.20 | Fraction of priced recs within budget (`budget_min × 0.8 .. budget_max × 1.2`). 0.5 (neutral) if no profile, no budget set, or no priced recs. |

Constants: `_WEIGHTS` (the table above), `_CONFIDENCE_MAP`, `_TARGET_RECS = 3`.

## Patterns & Gotchas

- **Never raises**: the whole body is wrapped in `try/except Exception`; on
  failure it returns `ScoringResult(total=0.5, breakdown={…all 0.5…}, warnings=[])`.
  Callers can rely on always getting a usable result.
- **Neutral 0.5 fallbacks**: `grounding`, `budget_fit` resolve to `0.5` when the
  needed data is absent (empty wine list / no profile / no budget / no priced
  recs). These are "cannot assess", not "bad" — distinct from the `0.0` returned
  when there are zero recommendations.
- **Empty wine list warning**: when `wine_list_text` is falsy, a warning string
  is appended (`"wine_list_text empty — grounding score is neutral"`).
- **Confidence normalisation**: `_normalize_confidence_level` lower-cases and
  matches a known level by `startswith`, so noisy LLM text like `"High — …"`
  still maps to `high`. Unrecognised levels score `0.5`.
- **Grounding fuzzy match** (`_is_grounded`): case-insensitive substring first,
  then ≥75% overlap of significant (≥3-letter) tokens as a fuzzy fallback.
- **Rounding**: `total` and each `breakdown` value are rounded to 4 decimal
  places for clean log output.
- **No API calls / deterministic**: safe to run on every recommendation request
  with no latency budget concern.

## Integration

Called post-recommendation (e.g. `routes/recommend.py`) for quality telemetry.
`cap_confidence=True` is passed for seed-derived profiles so the composite cannot
exceed the directional profile's own certainty — mirrors the prompt-side caveat
and the per-wine confidence cap.
