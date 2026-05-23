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
  avoided_styles: existing avoided_styles list from profile (optional; unused currently)
  Returns a PalateStats TypedDict.

def format_stats_for_prompt(stats: PalateStats) -> str
  Format a PalateStats dict as a structured text block for injection into the synthesis prompt.
  Returns a "STATISTICAL EVIDENCE" section string with frequency tables, style flags, and skew line.
```

## TypedDicts

### `FrequencyEntry`
```python
{"term": str, "count": int, "positive": int, "negative": int}
```

### `PriceStats`
```python
{"median": float, "p25": float, "p75": float, "count": int}
```

### `StyleSignals`
```python
{
  "natural_wine_affinity": bool,   # ≥2 notes contain natural wine markers
  "oxidative_affinity": bool,      # ≥2 notes contain oxidative markers
  "aging_preference": bool,        # ≥2 notes contain aging-preference markers
}
```

### `AspirationalSkew`
```python
{
  "cellar_over_consumed": list[str],  # terms over-represented in cellar vs consumed
  "summary_line": str,                # one-sentence prompt line, e.g. "buys Burgundy 2× more than consumed"
}
```

### `PalateStats`
```python
{
  "producer_frequency": list[FrequencyEntry],
  "region_frequency": list[FrequencyEntry],
  "varietal_frequency": list[FrequencyEntry],
  "price_distribution": dict,          # keys: "red", "white", "sparkling", "all" → PriceStats
  "style_signals": StyleSignals,
  "avoided_style_tokens": list[str],   # single-token distillation of disliked-wine patterns
  "top_producers": list[str],          # producers appearing ≥2× in positive notes
  "note_count": int,                   # total rows with a ConsumptionNote
  "aspirational_skew": AspirationalSkew,
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
| `_AVOIDED_STYLE_TOKEN_MAP` | Maps negative phrase patterns → single tokens (e.g., `"too oaky"` → `"oaky"`) |

## Aspirational Skew Computation

Compares term frequency in `inventory_rows` vs `consumed_rows` using a ratio threshold (≥1.5×). Terms appearing at least 2× more in the cellar than in the consumed-note history are flagged as aspirational. The `summary_line` is formatted as a single sentence for prompt injection.

## Integration Points

**Profile synthesis** (`profile.synthesize_palate_from_notes`):
- Called before the Claude synthesis call with `consumed_rows` and `inventory_rows`
- Result formatted via `format_stats_for_prompt()` and injected as "STATISTICAL EVIDENCE" into the synthesis prompt
- `avoided_style_tokens` and `top_producers` from stats are merged into the synthesized profile post-synthesis

**Recommendation route** (`routes/recommend.py`):
- Called at recommendation time with `consumed_rows` and `inventory_rows` to extract `aspirational_skew.summary_line`
- One-line summary passed to `build_system_prompt()` as `aspirational_skew`

## Patterns & Gotchas

- **Score scale auto-detection**: max score > 10 → 100-pt scale (positive threshold: ≥85); otherwise 5-pt (≥4.0). Avoids hardcoding.
- **Sentiment weighting**: frequency counts are split into `positive` and `negative` buckets. `top_producers` only uses positive notes (repeat-purchase signal).
- **Missing fields**: `ConsumptionNote`, `MasterVarietal`, `Region`, `Producer` are all treated as optional. Rows missing these fields are skipped gracefully.
- **No external calls**: entirely deterministic and synchronous. Safe to call on every recommendation request without latency budget.
