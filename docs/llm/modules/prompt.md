# prompt.py

## Responsibility

Construct the system prompt for Ollama. Embed taste profile, relevant cellar bottles, JSON schema, and recommendation instructions.

## Dependencies

<<<<<<< HEAD
- `profile.build_enhanced_profile_text()` (standard taste profile prose, no Ollama call)
- No other imports; bottle dicts are plain `dict`, not `models.Bottle`
=======
- `profile.build_enhanced_profile_text()` (taste profile prose)
- `models.Bottle` (for bottle fields)
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)

## Inputs/Outputs

**Inputs**:
- `relevant_bottles`: List of dicts matching style_terms (or top from inventory)
- `cellar_summary`: Prose summary of what user's cellar skews toward (e.g., "skews heavily toward Burgundy and Champagne")
- `taste_profile_override`: Optional pre-built profile string (from `build_enriched_profile_text()`). If provided, skips the internal `build_enhanced_profile_text()` call.
- `meal_hints`: Optional newline-separated pairing hints string (from `meal_to_wine_hints()`). Injected as `### TONIGHT'S MEAL` section.

**Outputs**: Complete system prompt string (1000+ words) with embedded JSON schema.

## Key Functions

**format_bottle(b)**: Return "{Vintage} {Producer} {Wine} (drink {Begin}–{End})". Skip empty fields.

**build_system_prompt(relevant_bottles, cellar_summary="", taste_profile_override=None, meal_hints="")**: 
  1. Use `taste_profile_override` if provided; otherwise call `build_enhanced_profile_text()`
  2. Format relevant bottles into bulleted list (max 20)
  3. Embed sommelier persona: 70% profile weight, 30% meal weight (explicit in prompt)
  4. Add HARD CONSTRAINT: recommendations must come from the restaurant list only
  5. Inject `### TONIGHT'S MEAL` section if `meal_hints` provided
  6. Embed JSON schema with field descriptions
  7. Append reasoning structure notes (4-step format) and confidence format note
  8. Return full prompt; also writes to `prompt.log` via dedicated `_prompt_logger`

<<<<<<< HEAD
## Profile Function Disambiguation

Two separate functions live in `profile.py`; `prompt.py` uses the first:

- **`build_enhanced_profile_text()`** — formats the frequency-derived taste profile as prose (no Ollama call). Called by `build_system_prompt()` when no `taste_profile_override` is provided.
- **`build_enriched_profile_text(ollama_url, ollama_model)`** — calls Ollama first to enrich the profile with multi-word style phrases, then formats. Called from `main.py` before the main recommendation call; the result is passed in as `taste_profile_override`.

`OWNER_PROFILE` (the hardcoded fallback string) lives in `profile.py`, not `prompt.py`.
=======
**OWNER_PROFILE**: Module-level constant string. Default taste profile text used when no CellarTracker data is loaded. Imported by `profile.py` as a fallback.
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)

## Reasoning Field Structure (enforced in prompt)

The prompt instructs the LLM to follow a 4-step structure for `reasoning`:
1. **Personal comparison** (required): `"Like your [owned bottle], but [how it differs/excels]."`
2. **Contrast** (where relevant): `"Unlike [avoided style/bottle], no [unwanted trait]."`
3. **Food context** (secondary): Meal synergy only if it adds genuine insight.
4. **Cellar note**: If outclassed by owned wine, or worth ordering despite similarity.

## Confidence Field Format (enforced in prompt)

`"[high|medium|low] — [single clause reason]"`  
Examples: `"high — hits your preference for grower Champagne with mineral complexity"` / `"medium — right style but the vintage may be too young"`

## Pattern & Gotchas

- **Sommelier persona**: "Be direct. No filler. Respond with ONLY valid JSON (no markdown, no backticks, no explanation)."
- **Priority weighting**: 70% profile / 30% meal is stated explicitly in the prompt to prevent meal overriding profile fit.
- **Prompt logging**: Every built prompt is written to `backend/prompt.log` via `_prompt_logger` (separate from the main sommelier logger, does not propagate). Useful for debugging prompt drift.
- **Schema in prompt**: Inline JSON schema prevents field name hallucination; also enforced via `_RESPONSE_SCHEMA` in recommender.py.
- **Confidence values**: Now free-form string with mandatory clause (not just "high|medium|low"). Validation is implicit via structured output schema in recommender.py.
- **Cellar context**: Notes if recommendation is outclassed by home inventory or worth ordering despite owning similar wines.
- **Relevant bottles**: Up to 20 shown; helps LLM avoid recommending something user already owns.

## Known Issues / TODOs

- No temperature/creativity control (delegated to Ollama defaults).
- Schema description is long; could be shortened or moved to docs.
- Cellar summary generation (in main.py) is heuristic-based; could be smarter.
- "Owner's cellar character" prefix suggests a generic owner; could personalize if auth added.

## Testing

Verify prompt is sent to Ollama with complete taste profile and cellar context. Check that LLM response attempts to honor schema constraints.
