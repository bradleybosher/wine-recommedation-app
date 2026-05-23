# retrieval.py

## Responsibility

Retrieval-augmented pre-filtering for large restaurant wine lists. When a wine list exceeds `_ACTIVATION_THRESHOLD` (40) lines after the coarse `filter_wine_list()` pass, rank each line by profile-signal overlap and return only the top `limit` lines for the recommendation prompt. No API calls — purely keyword-based.

## Dependencies

- `models.TasteProfile`
- `synonyms.expand_terms` — synonym/appellation expansion for regions and grapes
- `re`, `unicodedata`, `logging`

## Public Interface

```python
def rank_wine_list(
    wine_list_text: str,
    profile: TasteProfile,
    override_terms: Optional[list[str]] = None,
    limit: int = 40,
) -> str
```

**No-op conditions** (returns input unchanged):
- List has ≤ `limit` lines
- `profile` has no positive signals (returns first `limit` lines in this edge case)

## Scoring Algorithm

Per line:

| Signal | Score delta |
|---|---|
| Baseline (every line) | +0.25 |
| Top-producer name match | +2.0 per term |
| Preferred region/appellation term match | +1.5 per term |
| Preferred grape/varietal term match | +1.0 per term |
| Override term match | +1.0 per term |
| Preferred style descriptor match | +0.5 per term |
| Avoided-style token match | −2.0 per term |
| Price < 50 % of `budget_min` | −0.5 |
| Price > 200 % of `budget_max` | −0.5 |

**Tiered weights** reflect signal reliability: producers are the strongest positive (repeat-purchase signal), followed by region/appellation, then grape, then style descriptors.

**Synonym expansion**: region and grape terms are expanded via `synonyms.expand_terms()` before scoring. Example: `"Burgundy"` expands to include `"Marsannay"`, `"Côte de Nuits"`, `"Côte de Beaune"` etc.; `"Pinot Noir"` expands to include `"Spätburgunder"`.

**Producer matching** uses `profile.top_producers` (repeat-purchase producers derived from notes during synthesis). No synonym expansion — exact normalized substring match.

**Avoided-style tokens**: uses `profile.avoided_style_tokens` (single-token distillation of avoided-style sentences, e.g. `"oaky"`, `"jammy"`) rather than full sentences, so the penalty actually fires against typical one-line wine entries. Falls back to `profile.avoided_styles` if no tokens present.

**Currency symbols**: price extraction supports `$`, `£`, `€` prefixes.

Matching is accent-normalised (NFKD decomposition + combining character removal), case-insensitive substring matching.

Ties are broken by original list position (stable ordering).

## Integration Point

Called in `routes/recommend.py` after `filter_wine_list()` and invisible Unicode cleanup, before the system prompt is built. Only runs on the `winelist` source mode.

```python
wine_list_text = rank_wine_list(wine_list_text, taste_profile, override_terms=override_terms)
```

## Patterns & Gotchas

- **Token budget**: Target is 40 lines ≈ ≤4 KB of text in the prompt, well within Claude's context window for the recommendation task.
- **Price extraction**: Looks for `$NNN`, `£NNN`, `€NNN` patterns. Wines listed without a currency symbol are not price-scored.
- **Override terms**: Sourced from the `effective_style` form field (cellar_leans + temperament). Computed early in the recommend route so they're available for both retrieval and `get_relevant_bottles()`.
- **No re-ordering guarantee**: Top-scoring lines are returned in score order, not original menu order. Claude is unaffected; it scores wines against the profile regardless of list order.
- **Synonyms**: `expand_terms()` is applied to region and grape terms only — style descriptors and producers are matched as-is (producers are proper names; style terms are sensory phrases unlikely to appear verbatim in list entries).
- **No positive signals fallback**: When the profile has zero positive signals (no producers/regions/grapes/styles), the function truncates to the first `limit` lines rather than skipping entirely.
