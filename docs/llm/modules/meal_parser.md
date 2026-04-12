# meal_parser.py

## Responsibility

Parse a raw meal description string into a structured `MealProfile` dataclass, then format that profile as natural-language pairing hints for the system prompt. Acts as the structured bridge between user meal text and the LLM's pairing context.

## Dependencies

- Standard library only (`dataclasses`, `typing`)
- No external imports; no backend module imports

## Inputs/Outputs

**Inputs**: Raw meal description string (e.g., "pan-seared duck breast with cherry gastrique").

**Outputs**:
- `MealProfile` dataclass — structured fields for protein, cooking_method, sauce_flavor, heat_level, richness, dominant_flavors
- Prose hints string — formatted for inclusion in the system prompt `meal_section`

## Key Functions

**parse_meal_description(meal: str) → MealProfile**:
- Lowercases input; scans for known proteins, cooking methods, sauce flavors, heat keywords
- First match wins per category (no stacking)
- Returns MealProfile with defaults: heat_level="mild", richness="medium"

**meal_to_wine_hints(profile: MealProfile) → str**:
- Converts structured MealProfile to newline-separated hint lines
- Lines: protein + base_flavor, cooking method, sauce → dominant flavor seek, richness cue, heat cue
- Returns empty string if profile has no recognized fields (no hints injected)

**infer_wine_style_from_meal(profile: MealProfile) → List[str]**:
- Maps protein + richness combinations to wine style keywords (e.g., beef+rich → ["burgundy", "bordeaux", "barolo"])
- Used for style term inference; currently not wired into the main recommend flow

## Data Tables (lookup-driven design)

- **PROTEINS** — 13 entries: duck, beef, fish, salmon, chicken, lamb, pork, veal, seafood, shellfish, shrimp, lobster, crab → richness + base_flavor
- **COOKING_METHODS** — 9 entries: seared, roasted, braised, grilled, poached, pan-fried, steamed, raw, baked
- **SAUCE_FLAVORS** — 14 entries: cherry, gastrique, mushroom, cream, red wine reduction, beurre blanc, peppercorn, lemon, olive tapenade, truffle, soy, spice, tomato, butter → flavor + tannin_match
- **HEAT_KEYWORDS** — 8 entries: spicy, chili, cayenne, curry → "spicy"; pepper, peppercorn → "moderate"; garlic, herbs → "mild"

## Patterns & Gotchas

- **First-match-wins**: If meal contains both "salmon" and "beef", whichever appears first in `PROTEINS` iteration order wins. PROTEINS is a dict, so insertion order is preserved (Python 3.7+).
- **tannin_match field**: Present in SAUCE_FLAVORS but not currently used by `meal_to_wine_hints()` or the recommend endpoint. Future use.
- **infer_wine_style_from_meal**: Not called from `main.py`. Available utility but currently disconnected from the recommendation flow.
- **MealProfile dataclass vs. Pydantic model**: There is a `MealProfile` Pydantic model in `models.py` (for OpenAPI schema) and a `MealProfile` dataclass here (for internal use). They are structurally identical but separate types. The dataclass is used internally; the Pydantic model is for the SDK contract.
- **No NLP**: Pure keyword matching. "braised duck" matches, "slow-cooked duck" does not match "braised".

## Integration with main.py

```python
from meal_parser import parse_meal_description, meal_to_wine_hints

meal_hints = meal_to_wine_hints(parse_meal_description(meal))
system = build_system_prompt(relevant, cellar_summary=cellar_summary,
                             taste_profile_override=enriched_profile,
                             meal_hints=meal_hints)
```

## Known Issues / TODOs

- `infer_wine_style_from_meal()` is not connected to the recommendation flow (dead code for now).
- No fuzzy matching — "sear" won't match "seared"; "mushrooms" won't match "mushroom".
- Only one protein, one sauce, one cooking method matched per meal. Complex dishes underrepresented.
- `tannin_match` from SAUCE_FLAVORS is computed but never consumed.
