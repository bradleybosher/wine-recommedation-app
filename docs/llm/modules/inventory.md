# inventory.py

## Responsibility

Load/save user's wine cellar inventory (CellarTracker TSV export), filter by quantity and style keywords, compute cellar age.

## Dependencies

- `csv`, `io` (TSV parsing)
- `json`, `time` (caching to inventory.json)
- `unicodedata` (accent folding for matching)

## Inputs/Outputs

**Inputs**: CellarTracker TSV bytes (exported via CT app).

**Outputs**: 
- Parsed inventory: list of dicts (one per wine bottle)
- Inventory metadata: age_hours, stale flag

## Key Functions

**decode_cellartracker_upload(raw)** → str:
  - Try UTF-8, UTF-8-sig, cp1252, latin-1 encodings in order
  - Return decoded string or lossy fallback (UTF-8 with replace)
  - Used by both inventory and profile modules

**parse_ct_csv(csv_text)** → [dict]:
  - Delimiter: tab (TSV, not CSV)
  - Filter: keep only rows where Quantity > 0
  - Return list of dicts (keys = header names, values = string fields)

**save_inventory(csv_text)** → [dict]:
  - Parse CSV
  - Write to inventory.json: {"bottles": [...], "saved_at": timestamp}
  - Return bottles list

**load_inventory()** → Optional[dict]:
  - Load inventory.json
  - Calculate age_hours = (now - saved_at) / 3600
  - Return {"bottles": [...], "age_hours": float, "stale": age_hours > 168}
  - None if file missing

**get_relevant_bottles(bottles, style_terms)** → [dict]:
  - Map style keywords (Burgundy → ["pinot noir", "burgundy", "gevrey", ...])
  - Flatten to list of keywords
  - For each bottle: accent-fold Varietal, Appellation, Wine, Producer
  - Keep bottles matching any keyword
  - Return full bottle list if no keywords
  - Return filtered list otherwise

**_fold_for_match(text)** → str:
  - Lowercase + casefold
  - NFD normalize (decompose accents)
  - Strip combining marks (category Mn)
  - Result: "Côte-Rôtie" → "cote-rotie"
  - Handles Latin-based wine regions; won't work for Cyrillic/CJK

## Patterns & Gotchas

- **Quantity parsing**: String field, parsed as float. Strings like "2.5" or "1" both supported.
- **Quantity filtering**: ≤ 0 silently dropped (Quantity=0 or Quantity="" becomes no match).
- **Style map**: Hardcoded mapping (8 top regions/styles). Extensible but not dynamic.
- **Accent folding**: Case-insensitive substring match after accent normalization.
- **Cellar staleness**: age > 168 hours (7 days). No auto-refresh; user must re-upload.
- **Empty cellar**: Returns full bottle list if no style_terms provided (fallback behavior).

## Known Issues / TODOs

- Style map hardcoded (Burgundy, Chablis, etc.); could be stored externally.
- Accent folding only handles Latin base (French, Italian, Spanish). Fails on Georgian (Cyrillic) wine regions.
- Quantity zero silently drops; no warning to user.
- CellarTracker encoding sometimes cp1252 with BOM; decode_cellartracker_upload handles it but logs no warning.

## Testing

1. Upload CellarTracker list export (TSV with Quantity > 0).
2. Verify bottles loaded and age_hours calculated.
3. Call get_relevant_bottles with style_terms (e.g., ["burgundy"]).
4. Verify relevant bottles filtered correctly (case-insensitive, accent-tolerant).
