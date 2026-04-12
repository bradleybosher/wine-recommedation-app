# Glossary

## Domain Terms (Wine & CellarTracker)

**CellarTracker (CT)**: Wine inventory management app. Users export their cellar as TSV (tab-separated values) with standardized columns.

**Varietal**: Grape variety (Pinot Noir, Chardonnay, etc.). Often maps to preferred_grapes in taste profile.

**Appellation**: Geographic designation (Burgundy, Chablis, etc.). Often maps to preferred_regions.

**Vintage**: Year the wine was made.

**Tasting Notes**: User descriptions of a wine (e.g., "cherry, silky tannins, balanced acidity"). Analyzed to infer avoided_styles.

**Cellar Character**: Summary of what a user's inventory skews toward (e.g., "Burgundy and Bordeaux with strong Champagne representation").

**Drink Window**: BeginConsume–EndConsume. When a wine is optimal to drink.

**Score**: CT fields include CScore (critic), PScore (personal), CTScore (aggregate). Low score (<3.0) triggers avoided_styles inference.

## CellarTracker Export Types

**list**: Current cellar inventory. Has Quantity + iWine columns. Stable reference.

**consumed**: Wines drunk (tasted notes + rating).

**notes**: Dedicated tasting notes export. Has standalone Note column.

**purchases**: Purchase history. Has Price + Quantity, no standalone Note.

**unknown**: Unrecognized format.

## Application Terms

**Taste Profile**: Structured representation of user preference: varietals, regions, styles, descriptors, budget, avoided styles. Source: quiz, CellarTracker, or manual.

**Profile Data**: Raw merged profile_data.json. Contains export rows indexed by type (list, consumed, notes, purchases).

**Recommendation**: AI-generated top-3 wines matched to user profile + meal context. Each includes rank, wine_name, reasoning, confidence.

**Reasoning**: 2–4 sentence explanation of why a wine matches the profile. Must reference profile directly.

**Confidence**: high | medium | low. Subjective LLM assessment of match quality.

**List Quality Note**: Optional warning if wine list is limited (e.g., "No white selections").

**Relevant Bottles**: Subset of user's cellar matching the style_terms override or derived from profile. Used in system prompt to note if a recommendation is outclassed by home inventory.

**Style Terms**: Keywords (Burgundy, Chablis, Champagne, etc.) that expand to grape/appellation searches. Used to filter relevant bottles.

**Cache Key**: SHA256(wine_list_bytes, meal_text, inventory_hash, profile_hash). Prevents redundant LLM calls for identical requests.

**Avoided Styles**: Inferred from tasting notes rated ≤3.0. Examples: oaky, bitter, thin. Used in system prompt to avoid recommending these.

**Profile Match Summary**: One-sentence overview of how the recommendation set aligns with the user's taste profile.

**Confidence Badge**: UI element displaying recommendation.confidence as colored pill (high=green, medium=yellow, low=red).

## Implementation Terms

**Pydantic Model**: Python dataclass-like schema with validation. Used for all API input/output. Aliases allow camelCase JSON ↔ snake_case Python.

**System Prompt**: Instructions sent to Ollama before the wine list. Includes sommelier persona, taste profile, relevant bottles, JSON schema.

**User Prompt**: "My meal: {meal}\n\nWhat should I order?" sent to Ollama as user message.

**Ollama**: Local LLM inference engine. API endpoints: /api/chat (preferred), /api/generate (fallback).

**Response Cache**: SQLite table (response_cache). Stores JSON responses keyed by cache_key with timestamp. Busted on inventory/profile upload.

**Markdown Fences**: Code blocks (```json ... ```). LLMs often wrap JSON despite instructions. Stripped before json.loads().

**Accent Folding**: Normalize "Côte-Rôtie" → "cote-rotie" for matching. Handles Unicode combining marks.

**Inventory Staleness**: age_hours > 168. Flag if cellar data is >7 days old.

**Profile Staleness**: No explicit check, but profile_data.json is persistent until replaced.

## Abbreviations

- **CT**: CellarTracker
- **LLM**: Large Language Model
- **TSV**: Tab-Separated Values
- **JSON**: JavaScript Object Notation
- **JWT**: JSON Web Token (not used; auth out of scope)
- **SDK**: Software Development Kit (generated client code)
- **OpenAPI**: Specification for REST API contracts
- **Pydantic**: Python data validation library
- **DTO**: Data Transfer Object (models)
- **CORS**: Cross-Origin Resource Sharing
- **TTL**: Time To Live (7 days for inventory.json stale check)

## Operators & Field Names

**iWine**: CellarTracker's unique wine ID.

**Quantity**: Bottles available. Must be > 0 to be included.

**Producer**: Winery or producer name.

**Wine**: Specific wine name (e.g., "Sancerre", "Premier Cru").

**Color**: Red, white, rosé, sparkling, fortified, etc.

**Category**: Higher-level classification (TABLE_WINE, SPARKLING, FORTIFIED).

**Size**: Bottle size (750ml, 375ml, etc.).

**Price**: Purchase price.

**Value**: CT's appraised value.

**Currency**: USD, GBP, EUR, etc.

**Locale**: Where the bottle was purchased or is located.

**PNotes**: Producer notes (from CT database).

**CNotes**: Critic notes (from CT database).

**PScore**: Producer's rating.

**CScore**: Critic's rating.

**LikeVotes**: Thumbs-up count from CT users.

**LikePercent**: Percentage of CT users who liked it.

**LikeIt**: User's own thumbs-up/down.

**WindowSource**: Where the drink window was sourced.

**MasterVarietal**: Canonical varietal if Wine is a blend.

**Designation**: Specific designation (Reserve, Premier Cru, etc.).

**Vineyard**: Specific vineyard name if applicable.

**Country**, **Region**, **SubRegion**: Geographic hierarchy.

**BeginConsume**, **EndConsume**: Year range for optimal drinking.
