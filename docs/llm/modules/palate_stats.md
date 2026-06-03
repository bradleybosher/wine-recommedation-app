# palate_stats.py

## Responsibility

Pure-Python statistical analysis of CellarTracker consumed rows and inventory. Runs before the Claude synthesis call and produces grounded frequency counts, style signals, and aspirational skew data that are injected into the synthesis prompt as "STATISTICAL EVIDENCE". No LLM calls.

## Dependencies

- `collections.Counter`, `statistics` — frequency counting and median/quantile calculation
- No external imports

## Public Interface

```python
def compute_palate_stats(
    consumed_rows: list[dict],
    inventory_rows: list[dict] | None = None,
    avoided_styles: list[str] | None = None,
) -> PalateStats
  Compute statistical palate features from CellarTracker data.
  consumed_rows: rows from profile_data.json["consumed"]
  inventory_rows: rows from inventory.json["bottles"] (optional; needed for aspirational_skew)
  avoided_styles: existing avoided_styles sentences from profile (optional; distilled into
    avoided_style_tokens via _extract_avoided_tokens and merged with note-derived tokens)
  Returns a PalateStats TypedDict.

def format_stats_for_prompt(stats: PalateStats) -> str
  Format a PalateStats dict as a structured text block for injection into the synthesis prompt.
  Returns a "STATISTICAL EVIDENCE" section string with frequency tables, style flags, and skew line.
```

## TypedDicts

### `FrequencyEntry`
```python
{"total": int, "positive": int, "negative": int, "net": int}
```
`total` = appearances; `positive`/`negative` = sentiment-classified note counts;
`net` = positive − negative. The term itself is the dict key, not a field.

### `PriceStats`
```python
{"median": float, "p25": float, "p75": float, "count": int}
```

### `StyleSignals`
```python
{
  "natural_wine_affinity": bool,   # any note contains a natural-wine marker
  "oxidative_affinity": bool,      # any note contains an oxidative marker
  "aging_preference": bool,        # any note contains an aging-preference marker
  "value_driven": bool,            # any note contains a value marker (value/bargain/steal/…)
}
```

### `AspirationalSkew`
```python
{
  "over_represented": list[str],  # categories in the cellar at ≥1.5× their consumed rate
  "summary_line": str,            # one-sentence prompt line ("" when over_represented is empty)
}
```

### `PalateStats`
```python
{
  "producer_frequency": dict[str, FrequencyEntry],  # keyed by Producer
  "region_frequency":   dict[str, FrequencyEntry],  # keyed by Region
  "varietal_frequency": dict[str, FrequencyEntry],  # keyed by MasterVarietal
  "price_distribution": dict[str, PriceStats],       # keyed by raw Color field value
                                                     # ("Red","White","Rosé","Unknown",…) — no "all" bucket
  "style_signals": StyleSignals,
  "avoided_style_tokens": list[str],   # single-token distillation of disliked-wine patterns
  "top_producers": list[str],          # see Top Producers below
  "note_count": int,                   # len(consumed_rows)
  "aspirational_skew": AspirationalSkew | None,  # None when no inventory_rows supplied
}
```

## Keyword Lexicons

All matching is case-insensitive substring on the `ConsumptionNote` text.

| Lexicon | Used for |
|---|---|
| `_POSITIVE_SENTIMENT` | Identify "positive" notes to weight frequency counts |
| `_NEGATIVE_SENTIMENT` | Identify "negative" notes; source for avoided-style tokens |
| `_NATURAL_WINE_MARKERS` | `natural_wine_affinity` flag (`pét nat`, `brut nature`, `grower`, etc.) |
| `_OXIDATIVE_MARKERS` | `oxidative_affinity` flag (`oxidative`, `vin jaune`, `jura`, etc.) |
| `_AGING_MARKERS` | `aging_preference` flag (`needs time`, `more age`, `too young`, etc.) |
| (inline value set) | `value_driven` flag (`value`, `bargain`, `steal`, `great price`, `for the price`) |
| `_AVOIDED_STYLE_TOKEN_MAP` | Maps negative phrase patterns → single tokens (e.g., `"too oaky"` → `"oaky"`) |

## Aspirational Skew Computation

Compares varietal share in `inventory_rows` vs `consumed_rows`. A category is flagged into `over_represented` when its cellar share is ≥1.5× its consumed share, or when it holds >5% cellar share but was never consumed. Results are ranked by ratio and capped at the top 5. The `summary_line` names the top 3 (empty string when nothing qualifies). When no `inventory_rows` are supplied, `aspirational_skew` is `None` entirely.

## Integration Points

**Profile synthesis** (`profile.synthesize_palate_from_notes`):
- Called before the Claude synthesis call with `consumed_rows` and `inventory_rows`
- Result formatted via `format_stats_for_prompt()` and injected as "STATISTICAL EVIDENCE" into the synthesis prompt
- `avoided_style_tokens` and `top_producers` from stats are merged into the synthesized profile post-synthesis

**Recommendation route** (`routes/recommend.py`):
- Called at recommendation time with `consumed_rows` and `inventory_rows` to extract `aspirational_skew.summary_line`
- One-line summary passed to `build_system_prompt()` as `aspirational_skew`

## Top Producers

`top_producers` is `producer_frequency` sorted by `net` then `total` (both descending), filtered to producers with `total >= 2` (i.e. ≥2 total appearances — not positive-only), and capped at the top 10. Ties on net are broken by total appearance count.

## Patterns & Gotchas

- **Keyword-based sentiment**: each note is classified `positive`/`negative`/`neutral` by `_note_sentiment` (counts `_POSITIVE_SENTIMENT` vs `_NEGATIVE_SENTIMENT` substring hits). There is no numeric score-scale logic — the module never inspects a rating/score field, only `ConsumptionNote` text.
- **Sentiment weighting**: frequency entries split appearances into `positive`/`negative` counts and a signed `net`. `top_producers` ranks by net then total (see above).
- **Missing fields**: `ConsumptionNote`, `MasterVarietal`, `Region`, `Producer` are all treated as optional. Rows missing these fields are skipped gracefully.
- **No external calls**: entirely deterministic and synchronous. Safe to call on every recommendation request without latency budget.
