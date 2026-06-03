# insights.py

## Responsibility

Palate drift suggestion engine. Analyses the most recent recommendation flights for a profile and surfaces terms (grapes, regions) that Claude keeps recommending but the user hasn't articulated as preferences. No LLM calls — purely statistical analysis of saved flights.

## Dependencies

- `cache.DB_PATH` (SQLite database path)
- `models.PalateDriftSuggestion`
- `profile.build_taste_profile_pydantic`, `profile.load_profile_data`
- `json`, `logging`, `sqlite3`

## Public Interface

```python
def compute_drift_suggestions(profile_id: str) -> list[PalateDriftSuggestion]
```

Returns an empty list when:
- Fewer than `_MIN_FLIGHTS` (3) flights exist for the profile
- No term meets the `_MIN_HIT_RATE` (30 %) threshold

## Algorithm

1. Load the `_FLIGHT_WINDOW` (20) most recent flights from `flights` table via `response_json`.
2. Extract `grape` and `region` from every recommended wine across all flights.
3. Count how many distinct flights each term appeared in.
4. For each dimension (`preferred_grapes`, `preferred_regions`): find terms above the hit-rate threshold that are not already in the profile (substring-safe check — prevents duplicating "Pinot Noir" if profile has "Pinot").
5. Pick the single strongest signal per dimension.
6. Return at most one `PalateDriftSuggestion` per dimension — so at most **2** in practice (one for `preferred_grapes`, one for `preferred_regions`). The `_MAX_SUGGESTIONS = 3` cap is therefore never reached: it would only matter if a third dimension were added.

## Configuration Constants

| Constant | Value | Meaning |
|---|---|---|
| `_MIN_FLIGHTS` | 3 | Minimum flights before analysis runs |
| `_FLIGHT_WINDOW` | 20 | How many recent flights to examine |
| `_MIN_HIT_RATE` | 0.30 | Term must appear in ≥ 30 % of flights |
| `_MAX_SUGGESTIONS` | 3 | Cap on returned suggestions (unreachable — only 2 dimensions exist, so at most 2 are produced) |

## Output Shape (`PalateDriftSuggestion`)

```python
PalateDriftSuggestion(
    dimension="preferred_grapes",           # or "preferred_regions"
    current=["Pinot Noir", "Nebbiolo"],     # current profile values
    suggested=["Sangiovese"],               # newly surfaced term
    rationale="'Sangiovese' appeared in 7 of your last 20 recommendation flights...",
    supporting_flight_ids=["abc123", ...],  # flight IDs that drove this
)
```

## Integration Point

Registered at `GET /profile/insights` (in `routes/insights.py`). Returns `list[PalateDriftSuggestion]`. Requires Bearer JWT + `X-Profile-Id` header.

## Patterns & Gotchas

- **Hit-rate, not raw count**: A term appearing 4× in 4 different flights (20 % hit-rate) is not surfaced. One appearing in 6 of 20 flights (30 %) is. This avoids bias from flights with many recommendations.
- **Substring matching**: Profile check uses `tl in ex or ex in tl` to avoid suggesting "Pinot Noir" when "Pinot" is already present. Order-insensitive exact substring only — no stemming.
- **No LLM call**: Intentional. Drift suggestions are deterministic and auditable. The user can inspect `supporting_flight_ids` to verify the pattern.
- **Staleness**: Suggestions are computed live on each request — no cache. For high-traffic profiles, add a short-lived in-memory cache keyed by profile_id + latest flight timestamp.
