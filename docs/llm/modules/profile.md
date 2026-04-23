# profile.py

## Responsibility

Parse CellarTracker profile exports (TSV format), infer taste profile from consumption/notes history, and build prose summaries for system prompts.

## Dependencies

- `csv`, `io`, `json` (file parsing)
- `collections.Counter` (term frequency)
- `statistics.mean` (average spend)
- `unicodedata` (accent folding—imported but unused here; see inventory.py)
- `inventory.decode_cellartracker_upload()` (encoding fallback)

## Inputs/Outputs

**Inputs**: Raw bytes (CellarTracker TSV export).

**Outputs**: 
- `profile_data`: Raw dict indexed by export type (list, consumed, notes, purchases, unknown)
- Structured taste profile: dict with top_varietals, top_regions, preferred_descriptors, avoided_styles, avg_spend
- Prose summary: formatted paragraph for system prompt

## Key Functions

**ingest_export(raw)** → (type, rows):
  - Decode bytes (try UTF-8, cp1252, latin-1)
  - Detect export type from CSV headers (consumed, notes, list, purchases, unknown)
  - Parse TSV rows, normalize whitespace
  - Return export type + list of dicts

**save_profile_export(raw)** → type:
  - Ingest, merge into profile_data.json (keyed by type)
  - Write to file
  - Return type detected

**build_taste_profile(profile_data)** → dict:
  - Extract top 10 varietals from consumed wines (from Varietal / MasterVarietal)
  - Extract top 8 regions/subregions/appellations
  - Extract top 10 producers from all exports
  - Extract top 15 highly-rated wines (producer, wine, vintage)
  - Extract preferred descriptors: tokenize tasting notes, exclude stopwords, top 15 terms
  - Infer avoided_styles: detect score scale, scan low-scored notes, extract negative descriptors (bitter, oaky, thin, etc.), top 10 with freq ≥ 2
  - Calculate avg_spend from purchase price median (rounded to nearest 5)
  - Return dict with all above

**_infer_avoided_styles(profile_data)** → [str]:
  - First pass: collect all scores from notes + consumed exports to detect scale
  - If no scores present at all, return [] (skip inference)
  - Scale heuristic: `max_score > 10` → 1–100 scale, threshold `≤ 60`; otherwise 1–5 scale, threshold `≤ 3.0`
  - Logs detected scale at DEBUG: `score_scale_detected max_score=X threshold=Y`
  - Second pass: tokenize Note field for rows where score ≤ threshold
  - Keep only tokens in `negative_indicator_words` set (oaky, bitter, jammy, etc.)
  - Filter by freq ≥ 2
  - Return top 10

**build_enhanced_profile_text()** → str:
  - Load profile_data.json
  - Call build_taste_profile()
  - Format as prose paragraph (1–2 sentences per clause: varietals, regions, producers, descriptors, highly_rated, avg_spend)
  - Fallback to `OWNER_PROFILE` constant from prompt.py if no profile data

**build_taste_profile_pydantic(profile_data)** → TasteProfile:
  - Calls `build_taste_profile()` then maps result to a `TasteProfile` Pydantic model
  - Maps: top_varietals → preferred_grapes, top_regions → preferred_regions, preferred_descriptors → preferred_styles
  - Derives budget_min/max from avg_spend (±10 from rounded average)
  - Sets `profile_source="cellartracker"`
  - Returned in `UploadProfileResponse.taste_profile` so the frontend gets a typed profile immediately on upload

**enrich_profile_with_anthropic(raw, anthropic_api_key, anthropic_model)** → dict:
  - Takes raw dict from `build_taste_profile()`, calls Anthropic Claude via tool use for LLM enrichment
  - Prompt asks model to synthesise frequency tokens into multi-word style phrases + a `style_summary` sentence
  - Uses `enrich_taste_profile` tool with forced `tool_choice` — returns parsed dict directly (no JSON parsing)
  - Returns enriched dict with keys: `preferred_descriptors` (LLM phrases), `avoided_styles` (LLM phrases), `style_summary` (1 sentence)
  - Returns `raw` unchanged on any error (fully safe fallback)
  - `enrich_profile_with_ollama` is kept as an alias for backwards compatibility

**build_enriched_profile_text(anthropic_api_key, anthropic_model)** → str:
  - Orchestrates the full enrichment pipeline: load → build_taste_profile → enrich_profile_with_anthropic → format paragraph
  - Calls `enrich_profile_with_anthropic()` and prepends `style_summary` (if non-empty) to the paragraph
  - Fallback to `OWNER_PROFILE` if no data or enrichment empty
  - **This is the function called from main.py** — not `build_enhanced_profile_text()`

## Patterns & Gotchas

- **Score interpretation**: `_row_max_rating_score()` picks max from CScore, PScore, CTScore, MYscore. Assumes higher = better. Scale is inferred per-dataset (see `_infer_avoided_styles`).
- **Stopwords**: ~50 common English + wine-generic terms filtered from descriptors.
- **Negative indicators**: Hardcoded set of negative descriptors (oaky, bitter, thin, tannic, etc.). May miss domain-specific negatives.
- **Tasting note parsing**: Simple regex tokenization (`r"[a-zA-Z][a-zA-Z'-]*"`). May split hyphenated terms.
- **Oxford comma**: Formatting uses "A, B, and C" for readability.
- **Staleness**: No auto-refresh; profile_data.json persists until user re-uploads.
- **Empty profile**: Returns placeholder if profile_data is empty or has no rows. Fallback prose is generic.

## Patterns & Gotchas (additional)

- **Dual profile text functions**: `build_enhanced_profile_text()` formats from raw data only. `build_enriched_profile_text(api_key, model)` additionally calls Claude to synthesise richer phrases. Only the latter is used in the recommend flow.
- **OWNER_PROFILE fallback**: Imported from `prompt.py` as a lazy import inside the fallback branch to avoid circular imports.
- **Enrichment safety**: `enrich_profile_with_anthropic()` catches all exceptions and returns `raw` unchanged. No fixed timeout — Anthropic SDK handles it.
- **style_summary vs. paragraph**: If enrichment succeeds, `build_enriched_profile_text()` returns `"{style_summary} {paragraph}"`. If enrichment failed/empty, returns just the paragraph.

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b169158 (Added my profile tab)
**derive_taste_markers(descriptors)** → dict:
  - Joins all descriptor strings into a single lowercase text blob
  - Scores Acidity, Tannin, Body, and Oak on a 1–5 integer scale using keyword heuristics
  - Default score = 3 (medium); each matching high-indicator keyword adds 1, each low-indicator subtracts 1; clamped to [1, 5]
  - High/low keyword sets per dimension:
    - Acidity high: crisp, tart, bright, mineral, zesty, lively, laser, sharp, vivid, electric, piercing, racy, tense
    - Tannin high: tannic, grippy, structured, firm, chewy, muscular, angular, astringent, powerful, robust, tight
    - Body high: full, rich, generous, weighty, bold, concentrated, powerful, big, broad, dense, heavy
    - Oak high: oaky, toasty, vanilla, cedar, smoky, spiced, barrel, woody, buttery, creamy, toast
  - Returns dict with keys: `acidity`, `tannin`, `body`, `oak` — suitable for `TasteMarkers(**result)`
  - No LLM call; purely deterministic from descriptor tokens

<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> b169158 (Added my profile tab)
## Known Issues / TODOs

- Negative indicators hardcoded; should be tunable or learned.
- Score scale is heuristic (`max_score > 10` → 1–100); a dataset where all scores happen to be ≤ 10 on a 100-point scale would be mis-classified.
- Accent folding not used here (see inventory.py); could improve region matching.
- Producer deduplication: counts are case-sensitive (may double-count if CT data has mixed case).
- No weighting by vintage (old notes may not reflect current taste).
- `enrich_profile_with_anthropic()` timeout governed by Anthropic SDK defaults; not directly configurable here.

## Testing

1. Upload CellarTracker consumed export with tasting notes and scores.
2. Verify avoided_styles populated from low-scored notes.
3. Verify highly_rated matches top-rated wines.
4. Check prose summary grammar and formatting.
