# profile.py

## Responsibility

Parse CellarTracker profile exports (TSV format), infer taste profile from consumption/notes history, build prose summaries for system prompts, and manage per-profile data persistence under `PROFILES_DIR / profile_id /`.

## Constants

**PROFILES_DIR: Path** — Base directory for per-profile data; resolves to `backend/profiles/`.

## Dependencies

- `csv`, `io`, `json` (file parsing)
- `collections.Counter` (term frequency)
- `statistics.mean` (average spend)
- `unicodedata` (accent folding—imported but unused here; see inventory.py)
- `inventory.decode_cellartracker_upload()` (encoding fallback)
- `pathlib.Path` (profile_data file resolution)

## Inputs/Outputs

**Inputs**: Raw bytes (CellarTracker TSV export).

**Outputs**: 
- `profile_data`: Raw dict indexed by export type (list, consumed, notes, purchases, unknown)
- Structured taste profile: dict with top_varietals, top_regions, preferred_descriptors, avoided_styles, avg_spend
- Prose summary: formatted paragraph for system prompt

## Module-Level Cache

**_profile_cache**: `dict[str, tuple[float, dict]]`
  - Stores per-profile mtime-validated caches keyed by profile_id
  - Each entry is (mtime, data) to avoid re-reading profile_data.json on every request
  - `mtime` is the file modification time; compared on each load to detect file changes
  - Initialized to empty dict on module load; populated on first `load_profile_data(profile_id)` call
  - Invalidated per-profile by `bust_profile_cache(profile_id)` after any write

**_profile_path(profile_id: str) → Path**:
  - Helper that resolves to PROFILES_DIR / profile_id / profile_data.json
  - Used internally by load/save/bust functions

**_backup_path(profile_id: str) → Path**:
  - Helper that resolves to PROFILES_DIR / profile_id / profile_data.backup.json
  - Used by backup/restore functions

**bust_profile_cache(profile_id: str) → None**:
  - Resets `_profile_cache[profile_id]` to force next `load_profile_data(profile_id)` to read from disk
  - Called by: `save_profile_export()`, `persist_synthesized_profile()`, `write_profile_data()`, `restore_profile_backup()`, and endpoints in main.py
  - Ensures cached data doesn't become stale after file writes

## Key Functions

### Profile Loading & Persistence

**load_profile_data(profile_id: str) → dict**:
  - Load PROFILES_DIR / profile_id / profile_data.json
  - mtime-validated cache: if cached version has same mtime as disk file, return cached dict
  - Otherwise read from disk, cache with current mtime, and return
  - Return empty dict {} if file does not exist (fallback)

**write_profile_data(profile_id: str, data: dict) → None**:
  - Writes dict to PROFILES_DIR / profile_id / profile_data.json
  - Creates directory if absent
  - Busts profile cache via `bust_profile_cache(profile_id)`
  - Used by save_profile_export, persist_synthesized_profile, and endpoints

**save_profile_export(profile_id: str, raw: bytes) → str**:
  - Ingest raw bytes, merge into profile_data keyed by export type
  - Write to file via `write_profile_data()`
  - Returns export type detected (consumed, notes, list, purchases, unknown)

**backup_profile_data(profile_id: str) → bool**:
  - Copy PROFILES_DIR / profile_id / profile_data.json to profile_data.backup.json
  - Return True if a backup was written, False if no live file exists
  - Creates directory if absent

**restore_profile_backup(profile_id: str) → bool**:
  - Copy PROFILES_DIR / profile_id / profile_data.backup.json to profile_data.json
  - Bust profile cache via `bust_profile_cache(profile_id)`
  - Return False if no backup exists, True if restored

### Profile Export Parsing

**ingest_export(raw: bytes) → (type, rows)**:
  - Decode bytes (try UTF-8, cp1252, latin-1)
  - Validate minimal CellarTracker header column set: at least one of {wine, producer, appellation, varietal, vintage, quantity, note, consumed, iwine} must be present. Raises ValueError if unrecognised file format.
  - Detect export type from CSV headers (consumed, notes, list, purchases, unknown)
  - Parse TSV rows, normalize whitespace
  - Return export type + list of dicts

**build_taste_profile(profile_data: dict) → dict**:
  - **Short-circuit order** (first match wins):
    1. `profile_data["_synthesized"]` — LLM-synthesized CT palate produced by
       `synthesize_palate_from_notes(profile_id, ...)` at upload time. Same shape as the
       seed-bottle inferred profile, plus `palate_persona`.
    2. `profile_data["_inferred"]` — seed-bottle profile from
       `seed_profile.infer_profile_from_seeds()`.
    3. Fallback: deterministic frequency-token derivation (below).
  - Fallback derivation:
    - Extract top 10 varietals from consumed wines (from Varietal / MasterVarietal)
    - Extract top 8 regions/subregions/appellations
    - Extract top 10 producers from all exports
    - Extract top 15 highly-rated wines (producer, wine, vintage)
    - Extract preferred descriptors: tokenize tasting notes, exclude stopwords, top 15 terms
    - Infer avoided_styles: detect score scale, scan low-scored notes, extract negative descriptors (bitter, oaky, thin, etc.), top 10 with freq ≥ 2
    - Calculate avg_spend from purchase price median (rounded to nearest 5)
  - **Apply `_overrides`**: any keys in `profile_data["_overrides"]` are merged
    on top of the derived (or inferred) base via `apply_profile_overrides()`,
    so manual user edits made via `PATCH /profile` are reflected everywhere
    this function is consumed (recommendation prompt and `/profile-summary`).
  - Return dict with all above

**apply_profile_overrides(base, overrides)** → dict:
  - Shallow merge: each non-`None` top-level key in `overrides` replaces the
    corresponding value in `base`. Returns a new dict; `base` is not mutated.
  - Used by `build_taste_profile()` to layer user edits (PATCH /profile) on
    top of the derived/inferred profile.

**_infer_avoided_styles(profile_data)** → [str]:
  - First pass: collect all scores from notes + consumed exports to detect scale
  - If no scores present at all, return [] (skip inference)
  - Scale heuristic: `max_score > 10` → 1–100 scale, threshold `≤ 60`; otherwise 1–5 scale, threshold `≤ 3.0`
  - Logs detected scale at DEBUG: `score_scale_detected max_score=X threshold=Y`
  - Second pass: tokenize Note field for rows where score ≤ threshold
  - Keep only tokens in `negative_indicator_words` set (oaky, bitter, jammy, etc.)
  - Filter by freq ≥ 2
  - Return top 10

**build_enriched_profile_text_basic(profile_id: str) → str**:
  - Load profile_data via `load_profile_data(profile_id)`
  - Call `build_taste_profile()`
  - Format as prose paragraph (1–2 sentences per clause: varietals, regions, producers, descriptors, highly_rated, avg_spend)
  - Currency symbol uses USD ($), e.g. "typical spend $50–$70 per bottle"
  - Fallback to `OWNER_PROFILE` constant from prompt.py if no profile data
  - Non-enriched version; called by prompt.py as fallback when enrichment is not available

**build_taste_profile_pydantic(profile_data: dict) → TasteProfile**:
  - Calls `build_taste_profile(profile_data)` then maps result to a `TasteProfile` Pydantic model
  - Maps: top_varietals → preferred_grapes, top_regions → preferred_regions, preferred_descriptors → preferred_styles
  - Derives budget_min/max from avg_spend (±10 from rounded average)
  - Sets `profile_source="cellartracker"` or `"seed_bottles"` etc. based on source
  - Returned in `UploadProfileResponse.taste_profile` so the frontend gets a typed profile immediately on upload
  - Profile_id-agnostic; operates on already-loaded dict

**enrich_profile_with_anthropic(raw: dict, anthropic_api_key: str, anthropic_model: str) → dict**:
  - **Legacy fallback path**: only invoked when no `_synthesized` profile exists.
    The newer `synthesize_palate_from_notes()` subsumes this with richer context
    (raw notes vs. frequency tokens).
  - Takes raw dict from `build_taste_profile()`, calls Anthropic Claude via tool use for LLM enrichment
  - Prompt asks model to synthesise frequency tokens into multi-word style phrases + a `style_summary` sentence
  - Uses `enrich_taste_profile` tool with forced `tool_choice` — returns parsed dict directly (no JSON parsing)
  - Returns enriched dict with keys: `preferred_descriptors` (LLM phrases), `avoided_styles` (LLM phrases), `style_summary` (1 sentence)
  - Returns `raw` unchanged on any error (fully safe fallback)
  - Profile_id-agnostic; operates on dicts only
  - `enrich_profile_with_ollama` is kept as an alias for backwards compatibility

**synthesize_palate_from_notes(profile_id: str, profile_data: dict, anthropic_api_key: str, anthropic_model: str) → dict | None**:
  - **Primary LLM palate path for CellarTracker uploads.** Single Anthropic
    tool-use call (`synthesize_palate_profile`) that takes raw tasting notes
    grouped by score tier (high/mid/low, capped at 50 per tier) plus the
    deterministic structured signals (top varietals/regions/producers,
    highly_rated, avg_spend) and synthesizes a rich palate profile.
  - Returns dict shaped like seed-bottle inferred profile + extras:
    `preferred_descriptors` (multi-word phrases), `avoided_styles`,
    `style_summary`, `taste_markers` ({acidity, tannin, body, oak} 1-5),
    `palate_persona` (2-3 sentence sommelier persona naming signature styles),
    `inference_confidence`, `profile_source="cellartracker_synthesized"`,
    `note_count`.
  - Returns `None` when no notes are present (skip — fall back to deterministic).
  - **Raises** `anthropic.APIError` or `RuntimeError` on Claude-side failure —
    callers must catch and let the deterministic path take over.
  - Score-tier bucketing reuses the scale-detection heuristic from
    `_infer_avoided_styles`: max>10 → 100pt scale (high≥93, low≤85);
    otherwise 10pt scale (high≥9.0, low≤7.5).
  - Marks `inference_confidence="low"` and instructs Claude to be conservative
    when fewer than 10 notes are available.

**persist_synthesized_profile(profile_id: str, synthesized: dict) → None**:
  - Loads existing profile_data via `load_profile_data(profile_id)`, merges `synthesized` dict
    under the `_synthesized` key. Unlike `persist_seed_profile`, preserves the underlying CT rows
    (list/notes/consumed/purchases) — those are the synthesis source data.
  - Writes via `write_profile_data()` which busts the profile cache automatically.

**clear_synthesized_profile(profile_id: str) → None**:
  - Removes `_synthesized` from profile_data (loads, deletes key, writes back).
  - Busts profile cache via `bust_profile_cache(profile_id)`.
  - Called before a fresh synthesis attempt at `/upload-profile` so a failed
    Claude call doesn't leave stale synthesized data behind.

**build_enriched_profile_text(profile_id: str, anthropic_api_key: str, anthropic_model: str) → str**:
  - Orchestrates the full enrichment pipeline: load → build_taste_profile → enrich_profile_with_anthropic → format paragraph
  - Loads profile_data via `load_profile_data(profile_id)`, calls `build_taste_profile()`, then conditionally calls `enrich_profile_with_anthropic()`
  - Prepends `style_summary` (if non-empty) to the paragraph
  - **Short-circuits** the enrichment call when `profile_source` is
    `"seed_bottles"` or `"cellartracker_synthesized"` — those profiles already
    contain enriched fields and don't need a second LLM pass.
  - Fallback to `OWNER_PROFILE` if no data or enrichment empty
  - **This is the function called from routes/recommend.py** — not `build_enriched_profile_text_basic()`

## Patterns & Gotchas

- **Per-profile data layout**: All profile data lives under `PROFILES_DIR / profile_id /`. The `_profile_path()` and `_backup_path()` helpers abstract this structure.
- **Profile cache is per-profile**: `_profile_cache` is now a dict keyed by profile_id. Each entry is mtime-validated. Calling `bust_profile_cache(profile_id)` invalidates only that profile's cache entry.
- **Backup/restore**: Backup files live as `.backup.json` siblings to the live `profile_data.json`. No cleanup; backups must be managed externally if desired.
- **Score interpretation**: `_row_max_rating_score()` picks max from CScore, PScore, CTScore, MYscore. Assumes higher = better. Scale is inferred per-dataset (see `_infer_avoided_styles`).
- **Stopwords**: ~50 common English + wine-generic terms filtered from descriptors.
- **Negative indicators**: Hardcoded set of negative descriptors (oaky, bitter, thin, tannic, etc.). May miss domain-specific negatives.
- **Tasting note parsing**: Simple regex tokenization (`r"[a-zA-Z][a-zA-Z'-]*"`). May split hyphenated terms.
- **Oxford comma**: Formatting uses "A, B, and C" for readability.
- **Staleness**: No auto-refresh; profile_data.json persists until user re-uploads.
- **Empty profile**: Returns placeholder if profile_data is empty or has no rows. Fallback prose is generic.
- **Dual profile text functions**: `build_enriched_profile_text_basic(profile_id)` formats from raw data only. `build_enriched_profile_text(profile_id, api_key, model)` additionally calls Claude to synthesise richer phrases. Only the latter is used in the recommend flow.
- **OWNER_PROFILE fallback**: Imported from `prompt.py` as a lazy import inside the fallback branch to avoid circular imports.
- **Enrichment safety**: `enrich_profile_with_anthropic()` catches all exceptions and returns `raw` unchanged. No fixed timeout — Anthropic SDK handles it.
- **style_summary vs. paragraph**: If enrichment succeeds, `build_enriched_profile_text()` returns `"{style_summary} {paragraph}"`. If enrichment failed/empty, returns just the paragraph.
- **Profile_id-agnostic functions**: `build_taste_profile()`, `apply_profile_overrides()`, `build_taste_profile_pydantic()`, `enrich_profile_with_anthropic()`, and `derive_taste_markers()` all operate on dicts only; they do not read/write files or know about profile_id. This keeps the taste-building logic reusable across seed profiles and inferred profiles too.

**derive_taste_markers(descriptors: list[str]) → dict**:
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
  - Profile_id-agnostic; used by synthesize_palate_from_notes to populate taste_markers
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
