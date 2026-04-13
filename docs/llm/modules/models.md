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

### WineRecommendation

Single ranked wine recommendation.

Fields:
- `rank`: int (1–3)
- `wine_name`: str (required)
- `producer`, `region`: Optional[str]
- `vintage`: Optional[int] (year, not string)
- `price`: Optional[float]
- `reasoning`: str (2–4 sentences, specific to profile match)
- `confidence`: str ("high" | "medium" | "low")

### RecommendationResponse

Full recommendation set returned by `/recommend`.

Fields:
- `recommendations`: List[WineRecommendation] (up to 3)
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
- `meal`: str (required)
- `style_terms`: Optional[str] = "" (comma-separated override terms)

### MealProfile (Pydantic)

OpenAPI/SDK-facing schema for meal analysis result. Structurally identical to the `MealProfile` dataclass in `meal_parser.py` but kept separate.

Fields:
- `protein`, `cooking_method`, `sauce_flavor`: Optional[str]
- `heat_level`: str = "mild"
- `richness`: str = "medium"
- `dominant_flavors`: List[str]

### TasteMarkers

Heuristic taste-marker scores derived from the user's preferred descriptors. Each field is an int on a 1–5 scale (1 = very low, 5 = very high).

Fields:
- `acidity`: int
- `tannin`: int
- `body`: int
- `oak`: int

### CellarStats

Aggregate statistics computed from the user's cellar inventory at request time.

Fields:
- `total_bottles`: int (sum of quantities)
- `unique_wines`: int (number of distinct bottle rows)
- `vintage_oldest`: Optional[int]
- `vintage_newest`: Optional[int]

### ProfileSummaryResponse

Returned by `GET /profile-summary`. Derived taste profile plus enriched data.

Fields:
- `top_varietals`, `top_regions`, `top_producers`: List[str]
- `highly_rated`: List[Dict[str, str]] (producer, wine, vintage per item)
- `preferred_descriptors`, `avoided_styles`: List[str]
- `avg_spend`: Optional[int] (rounded to nearest 5)
- `style_summary`: Optional[str] — Ollama-generated one-sentence palate portrait; null if Ollama unavailable
- `taste_markers`: Optional[TasteMarkers] — heuristic scores derived from descriptors
- `cellar_stats`: Optional[CellarStats] — computed from inventory at request time

## Patterns

All models use `ConfigDict(alias_generator=to_camel, populate_by_name=True)`:
- JSON: camelCase (e.g., `wineRecommendation`, `listQualityNote`)
- Python: snake_case (e.g., `wine_recommendation`, `list_quality_note`)
- Both accepted on input

All fields Optional unless marked required (enables graceful degradation).

## Gotchas

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
