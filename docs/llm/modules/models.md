# models.py

## Responsibility

Pydantic v2 data models for all API input/output validation. Schemas serve as contracts between backend and frontend.

## Dependencies

- `pydantic` (BaseModel, Field, ConfigDict, alias_generator)
- `pydantic.alias_generators.to_camel` (auto-case conversion)

## Models

### Bottle (CellarTracker Fields)

All fields Optional[str] (CellarTracker exports as strings, even when numeric).

Key fields:
- `iWine`: Unique wine ID
- `Vintage`, `Producer`, `Wine`: Core identification
- `Varietal`, `Appellation`: Grape + region
- `Quantity`, `TotalQuantity`: Bottle count (filtered > 0)
- `Price`, `Value`, `Currency`: Pricing
- `BeginConsume`, `EndConsume`: Drink window (strings, e.g., "2024", "2030")
- `PNotes`, `CNotes`: Producer/critic notes
- `PScore`, `CScore`, `LikePercent`: Ratings

Config: camelCase JSON, snake_case Python (via `populate_by_name=True`).

### TasteProfile

User preference model, source-agnostic (quiz, CellarTracker, manual).

Fields:
- `preferred_styles`, `preferred_regions`, `preferred_grapes`, `avoided_styles`: List[str]
- `budget_min`, `budget_max`: Optional[float]
- `occasion`, `food_pairing`: Optional[str] (context hints)
- `profile_source`: str (informational: "manual", "cellartracker", "quiz", etc.)
- `inference_confidence`: Optional[str] — "high"|"medium"|"low", only set when profile_source=="seed_bottles"

### Coords

Approximate lat/lon of a wine's production region.

Fields:
- `lat`: float
- `lon`: float

### DrinkWindow

Estimated drinking window in integer years.

Fields:
- `from_year`: int — Python alias for the `"from"` JSON key (reserved keyword workaround). `Field(alias="from")` with `populate_by_name=True` allows Python constructors to use `from_year=` while JSON serializes as `"from"`.
- `peak`: int
- `until`: int

Note: No `alias_generator=to_camel` on this model — fields are single-word or use explicit alias above.

### WineColor

Hex palette for a recommended wine, derived server-side (never requested from Claude).

Fields:
- `glass`: str — primary wine colour hex
- `tint`: str — light background tint hex
- `ink`: str — dark ink colour hex
- `accent`: str — accent colour hex

### StructureBars

Wine structure profile (0–10 scale each).

Fields:
- `tannin`, `acidity`, `body`, `sweetness`, `oak`: float

### Critic

Approximate critic score.

Fields:
- `score`: float
- `source`: str

### WineRecommendation

Single ranked wine recommendation (Phase 5+: full enrichment fields).

Core fields:
- `rank`: int (1–3)
- `wine_name`: str (required)
- `producer`, `region`: Optional[str]
- `vintage`: Optional[int] (year, not string)
- `price`: Optional[float] — `coerce_price` validator strips currency symbols (e.g., `"$45.00"` → `45.0`)
- `reasoning`: str (2–4 sentences, structured: personal comparison → contrast → food → cellar note)
- `confidence`: str ("high|medium|low — single clause reason")
- `fits`: Optional[List[str]] — 2–3 short tags grounding pick in concrete profile signals; omitted when no clean match (renamed from `fit_markers`)

Enrichment fields (all Optional, populated by Claude via tool use):
- `appellation`: Optional[str] — official AOC/DOC/AVA designation
- `country`: Optional[str]
- `coords`: Optional[Coords]
- `grape`: Optional[str] — primary variety
- `abv`: Optional[float]
- `drink`: Optional[DrinkWindow]
- `color`: Optional[WineColor] — **backend-derived only**; not requested from Claude (avoids hallucinated hex codes); populated by `recommender._derive_color()` post-validation
- `bars`: Optional[StructureBars]
- `wheel`: Optional[Dict[str, int]] — 6–8 aroma entries, intensity 0–10
- `nose`: Optional[str] — one sentence aromatic profile
- `palate`: Optional[str] — one sentence palate and finish
- `pairs`: Optional[List[str]] — 2–4 food pairing suggestions
- `critic`: Optional[Critic]

### RecommendationResponse

Full recommendation set returned by `/recommend`.

Fields:
- `recommendations`: List[WineRecommendation] (up to N, default 3)
- `list_quality_note`: Optional[str] (warning if list is limited, e.g., "No reds")
- `profile_match_summary`: str (1 sentence overview)

### InventoryResponse

Returned by `GET /inventory`.

Fields:
- `bottles`: List[Bottle]
- `age_hours`: Optional[float] (hours since last upload)
- `stale`: bool (age > 168 hours)

### UploadInventoryResponse

Acknowledgment of inventory upload.

Fields:
- `count`: Bottle count saved
- `message`: Confirmation string

### UploadProfileResponse

Acknowledgment of profile upload — now includes typed taste profile.

Fields:
- `export_type`: CellarTracker export type detected ("list", "consumed", "notes", "purchases", "unknown")
- `message`: Confirmation string
- `taste_profile`: `Optional[TasteProfile]` — derived from uploaded data immediately; null if derivation fails

### RecommendRequest

Request body model for the `/recommend` endpoint (used internally; FormData on the wire).

Fields:
- `meal`: str (default "")
- `style_terms`: Optional[str] = "" (comma-separated override terms)

### TasteMarkers

Heuristic taste-marker scores derived from the user's preferred descriptors. Each field is an int on a 1–5 scale (1 = very low, 5 = very high).

Fields:
- `acidity`, `tannin`, `body`, `oak`: int

### CellarStats

Aggregate statistics computed from the user's cellar inventory at request time.

Fields:
- `total_bottles`, `unique_wines`: int
- `vintage_oldest`, `vintage_newest`: Optional[int]

### ProfilePatchRequest

Request body for `PATCH /profile`. Any subset of fields may be provided; non-`None` fields are merged into `profile_data.json["_overrides"]` and layered on top of the derived/inferred profile by `build_taste_profile()`. All fields default to `None`.

Fields:
- `top_varietals`, `top_regions`, `preferred_descriptors`, `avoided_styles`: Optional[List[str]]
- `avg_spend`: Optional[int]
- `style_summary`: Optional[str]
- `taste_markers`: Optional[TasteMarkers]

### ProfileSummaryResponse

Returned by `GET /profile-summary`. Derived taste profile plus enriched data.

Fields:
- `top_varietals`, `top_regions`, `top_producers`: List[str]
- `highly_rated`: List[Dict[str, str]] (producer, wine, vintage per item)
- `preferred_descriptors`, `avoided_styles`: List[str]
- `avg_spend`: Optional[int] (rounded to nearest 5)
- `style_summary`: Optional[str] — Anthropic-generated one-sentence palate portrait; null if unavailable
- `taste_markers`: Optional[TasteMarkers] — heuristic scores derived from descriptors
- `cellar_stats`: Optional[CellarStats] — computed from inventory at request time
- `profile_source`: Optional[str] — "cellartracker" | "seed_bottles" | "manual"
- `inference_confidence`: Optional[str] — populated only when profile_source == "seed_bottles"
- `seed_bottle_count`: Optional[int] — number of seed bottles when profile is seed-derived

### MealProfile (Pydantic)

OpenAPI/SDK-facing schema for meal analysis result. Structurally identical to the `MealProfile` dataclass in `meal_parser.py` but kept separate.

Fields:
- `protein`, `cooking_method`, `sauce_flavor`: Optional[str]
- `heat_level`: str = "mild"
- `richness`: str = "medium"
- `dominant_flavors`: List[str]

## Patterns

All models use `ConfigDict(alias_generator=to_camel, populate_by_name=True)`:
- JSON: camelCase (e.g., `wineRecommendation`, `listQualityNote`)
- Python: snake_case (e.g., `wine_recommendation`, `list_quality_note`)
- Both accepted on input

Exception: `DrinkWindow` uses `ConfigDict(populate_by_name=True)` only (no `alias_generator`) because the `from` field requires an explicit `Field(alias="from")`.

All fields Optional unless marked required (enables graceful degradation).

## Gotchas

- **`from` reserved keyword**: `DrinkWindow.from_year` uses `Field(alias="from")`. Python constructors use `from_year=`; JSON serializes as `"from"`. `populate_by_name=True` is required for this to work.
- **`color` field**: Excluded from the Claude tool schema — never asked of the LLM. Populated server-side by `recommender._derive_color()` after Pydantic validation. This avoids hallucinated hex codes.
- **`fits` (formerly `fit_markers`)**: Renamed in Phase 5. Frontend must use `wine.fits`, not `wine.fitMarkers`.
- **Vintage field**: int (year), not string. JSON parse must coerce.
- **Confidence values**: Free-form string with required explanatory clause (e.g. `"high — hits your preference for grower Champagne"`). Not an enum; enforced by prompt/schema, not Pydantic.
- **Price**: float, nullable. `WineRecommendation.coerce_price` field validator strips currency symbols before coercion (e.g., `"$45.00"` → `45.0`).
- **Reasoning**: Long string (2–4 sentences). No max length enforced (could be 1000+ chars).
- **CellarTracker fields**: All strings, even numeric (e.g., Quantity="2.5"). Parse upstream as needed.
- **MealProfile dual definition**: There is a `MealProfile` Pydantic model here (for OpenAPI/SDK) and a `MealProfile` dataclass in `meal_parser.py` (for internal use). They are structurally identical but separate types. Do not conflate them.

## Testing

1. Validate that Pydantic rejects invalid RecommendationResponse (missing rank, invalid confidence, etc.).
2. Test camelCase ↔ snake_case conversion both directions.
3. Verify Optional fields serialize as null in JSON when not provided.
4. Verify `DrinkWindow` round-trips correctly: Python `from_year=2022` → JSON `{"from": 2022}` → Python `from_year=2022`.
5. Verify `color` is never null on a returned `WineRecommendation` (always populated by `_derive_color`).
