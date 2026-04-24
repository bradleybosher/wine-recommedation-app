# inventory.py

## Responsibility

<<<<<<< HEAD
Load/save user's wine cellar inventory (CellarTracker TSV export); pre-filter restaurant wine lists to remove non-wine lines; score and rank cellar bottles against restaurant style signals and owner taste preferences.
=======
Load/save user's wine cellar inventory (CellarTracker TSV export), filter by quantity and style keywords, compute cellar age.
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)

## Dependencies

- `csv`, `io` (TSV parsing)
<<<<<<< HEAD
- `json`, `time` (caching to `inventory.json`)
- `datetime` (drinking window comparison)
- `unicodedata`, `re` (accent folding, regex patterns)
- `models.TasteProfile` (type hint only — profile not used in filtering logic)

## Inputs/Outputs

**Inputs**:
- CellarTracker TSV bytes (exported via the CT app)
- Raw restaurant wine list text (from `parser.py`)
- Owner taste preferences dict (from `profile.build_taste_profile()`)

**Outputs**:
- Parsed inventory: `list[dict]` (one dict per bottle, keys = CellarTracker header names)
- Filtered wine list: `str` (non-wine lines removed)
- Relevant bottles: `list[dict]` (scored and ranked subset of inventory)

---

## Constants

**`_WINE_STYLE_KEYWORDS`** — 200+ known wine terms: red/white varietals, sparkling types, regions (Burgundy, Barolo, Napa, etc.), blends, and style descriptors. Used in `filter_wine_list()` and `extract_terms_from_wine_list_text()`. All matching is accent-folded and case-insensitive.

**`_WINE_ESTATE_WORDS`** — Producer structural words: `château`, `domaine`, `clos`, `tenuta`, `weingut`, `winery`, `vineyard`, `cantina`, etc. Pre-folded into `_FOLDED_ESTATE_WORDS` at module load.

**`_FOOD_KEYWORDS`** — Cooking methods and dish categories that never appear in wine names: `grilled`, `braised`, `risotto`, `salmon`, `served with`, etc. Used as a food-override signal in `_is_wine_line()`.

**`_NON_WINE_BEVERAGE_KEYWORDS`** — Spirits, liqueurs, beer, cocktail, and non-alcoholic keywords: `whisky`, `bourbon`, `vodka`, `lager`, `ipa`, `cocktail`, `espresso`, `sparkling water`, etc. Used in `_is_non_wine_beverage()`.

**`_VINTAGE_RE`** — Regex matching years 1990–2029. Specifically avoids matching founding years, table numbers, or anything outside a plausible wine vintage range.

**`_VINTAGE_EXCLUSION_RE`** — Regex matching context that turns a year into a non-vintage date: `Est.`, `Since`, `Founded`, `©`, etc.

**`_STYLE_MAP`** — Backward-compatibility expansion map for `override_terms` (e.g., `"burgundy"` → `["pinot noir", "burgundy", "bourgogne", "gevrey", "chambolle"]`). Not used in the primary filtering path.

---

## Key Functions

### Inventory CRUD

**`decode_cellartracker_upload(raw: bytes) → str`**
- Try UTF-8-sig, UTF-8, cp1252, latin-1 in order
- Return decoded string; lossy UTF-8 fallback if all fail
- Used by both `inventory.py` and `profile.py`

**`parse_ct_csv(csv_text: str) → list[dict]`**
- Delimiter: tab (CT exports TSV, not CSV)
- Filter: keep only rows where `Quantity > 0`
- Return list of dicts (keys = header names, values = strings)

**`save_inventory(csv_text: str) → list[dict]`**
- Parse CSV, write to `inventory.json`: `{"bottles": [...], "saved_at": timestamp}`
- Return bottles list

**`load_inventory() → dict | None`**
- Load `inventory.json`; return `None` if missing
- Calculate `age_hours = (now - saved_at) / 3600`
- Return `{"bottles": [...], "age_hours": float, "stale": age_hours > 168}`

### Text Normalisation

**`_fold_for_match(text: str) → str`**
- Lowercase + casefold → NFD decompose → strip combining marks (category `Mn`)
- Result: `"Côte-Rôtie"` → `"cote-rotie"`
- Used throughout for accent-tolerant matching

### Wine List Keyword Extraction

**`extract_terms_from_wine_list_text(text: str) → list[str]`**
- Scan raw restaurant wine list text for matches in `_WINE_STYLE_KEYWORDS`
- Deduplicates, then returns sorted longest-first (multi-word terms before component words)
- Output is used as `restaurant_terms` for `get_relevant_bottles()`

### Wine List Pre-Filter

**`filter_wine_list(wine_list_text: str, _profile: TasteProfile | None) → str`**

Two-phase pipeline that strips non-wine content before the text reaches the LLM.

**Phase 0 — unconditional drops:**
- `_is_floating_currency(line)` → drops price-only rows (`$45`, `175 / 250`)
- `_is_non_wine_beverage(line, folded_wine_keywords)` → drops spirit/beer/cocktail/non-alcoholic lines that carry no wine signal

**Phase 1 — dictionary pass:**
- `_is_wine_line(line, folded_wine_keywords)` → keeps lines that have at least one of: vintage year (1990–2029), wine keyword, or estate structural word; drops lines that only have a keyword/estate word AND also contain a food keyword

Returns filtered text — one entry per line, blank lines removed. Falls back to original text on any unexpected error (never raises).

#### Helper predicates

**`_is_floating_currency(line: str) → bool`**
- True if line contains only price/currency characters (`£`, `$`, `€`, `/`, `|`, digits, spaces)
- Requires at least one digit and one currency symbol or separator

**`_is_food_line(line: str) → bool`**
- True if line contains any token from `_FOOD_KEYWORDS`

**`_is_non_wine_beverage(line: str, folded_wine_keywords: list[str]) → bool`**
- True when line contains a non-wine beverage keyword AND has neither a vintage year nor a wine keyword
- Dual check prevents false positives on "Grappa di Barolo" (has wine keyword) or "2019 Brandy-oaked Chardonnay" (has vintage)

**`_is_wine_line(line: str, folded_wine_keywords: list[str]) → bool`**
- Signals checked (in order): vintage year → wine keyword → estate word
- Food override: if no vintage present and `_is_food_line()` fires, returns False
- Example dropped: `"Pan-roasted duck with Barolo reduction"` (food keyword, no vintage)
- Example kept: `"2019 Château Margaux"` (vintage present, food override cannot fire)

### Cellar Bottle Scoring

**`_score_bottle(bottle: dict, restaurant_terms: list[str], profile_prefs: dict, current_year: int) → float`**

Scoring weights:
| Signal | Score |
|---|---|
| Profile `preferred` term match | +1.5 per term |
| `restaurant_terms` match | +1.0 per term |
| Drinking window open (`BeginConsume ≤ now ≤ EndConsume`) | +0.5 |
| Too young (`now < BeginConsume`) | −0.3 |
| `avoided` style matched | `float("-inf")` (hard exclusion) |

Fields searched: `Varietal`, `Appellation`, `Wine`, `Producer`, `Region`, `SubRegion` — all accent-folded.

**`get_relevant_bottles(bottles, restaurant_terms, profile_prefs, override_terms=None, limit=30) → list[dict]`**
- Score every bottle with `_score_bottle()`
- Drop hard-excluded bottles (`score == float("-inf")`)
- Sort by score descending
- Return top `limit` bottles (default 30)
- `override_terms`: when provided, expanded via `_STYLE_MAP` and used in place of `restaurant_terms`

---

## Patterns & Gotchas

- **Quantity parsing**: `Quantity` is a string field; parsed as `float`. `"2.5"` and `"1"` both work. Rows with Quantity ≤ 0 or empty are silently dropped.
- **Profile not used in `filter_wine_list()`**: The `_profile` parameter is accepted for signature compatibility but intentionally ignored — ranking against preferences is the LLM's job, not the pre-filter's.
- **Food override requires no vintage**: A line with both a vintage year and a food keyword (e.g., `"2019 Duck Confit Pinot Noir"`) is NOT dropped — the vintage signal dominates.
- **`_is_non_wine_beverage` requires dual evidence**: Both a non-wine keyword AND absence of wine signal must be present. This prevents false positives on liqueur-style wine names.
- **Cellar staleness**: `age > 168 hours` (7 days). No auto-refresh; user must re-upload.
- **Accent folding**: Handles Latin-based regions (French, Italian, Spanish). Will not work correctly for Cyrillic or CJK wine regions.
- **`_STYLE_MAP` is for override_terms only**: The primary filtering path uses `restaurant_terms` directly from `extract_terms_from_wine_list_text()`.

## Known Issues / TODOs

- Style map hardcoded; could be stored externally or extended.
- No warning to user when Quantity zero silently drops rows.
- CellarTracker encoding sometimes cp1252 with BOM — `decode_cellartracker_upload` handles it but logs no warning.
- Accent folding only handles Latin base; fails on Georgian (Cyrillic) wine regions.

## Testing

1. Upload CellarTracker TSV with Quantity > 0 rows; verify `load_inventory()` returns correct `age_hours` and `stale` flag.
2. Call `filter_wine_list()` on a wine list containing spirit/beer/food/price lines; verify only wine lines survive.
3. Call `get_relevant_bottles()` with profile prefs containing avoided styles; verify those bottles return `float("-inf")` and are excluded from output.
4. Verify `extract_terms_from_wine_list_text()` returns multi-word terms before single-word terms from the same text.
=======
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
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
