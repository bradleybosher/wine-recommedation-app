# prompt.py

## Responsibility

Construct the system prompt for Claude. Embed taste profile, relevant cellar bottles, JSON schema, meal hints, and constraint injection (bottle count, budget ceiling).

## Dependencies

- `profile.build_enriched_profile_text_basic()` (standard taste profile prose, non-enriched version)
- No other imports; bottle dicts are plain `dict`, not `models.Bottle`

## Inputs/Outputs

**Inputs** (`build_system_prompt`):
- `relevant_bottles`: List of dicts matching style_terms (or top from inventory)
- `cellar_summary`: Prose summary of what user's cellar skews toward (e.g., "skews heavily toward Burgundy and Champagne")
- `taste_profile_override`: Optional pre-built profile string (from `build_enriched_profile_text()`). If provided, skips the internal `build_enriched_profile_text_basic()` call.
- `meal_hints`: Optional newline-separated pairing hints string (from `meal_to_wine_hints()`). Injected as `### TONIGHT'S MEAL` section.
- `profile_source`: One of `"cellartracker"` (default), `"seed_bottles"`, `"manual"`. When `"seed_bottles"`, a one-line caveat is prepended to the taste-profile block instructing the model to treat signals as directional, not authoritative.
- `bottle_count`: int (default 3) — injected into the `CONSTRAINTS` block as "Return exactly N ranked recommendations."
- `budget_ceiling`: str (default "") — when non-empty, injected into `CONSTRAINTS` as "Budget ceiling per bottle: X — exclude wines above this price."
- `taste_markers`: `dict | None` — `{acidity, tannin, body, oak}` 1-5 integer scores from the synthesized/seed profile. When present, rendered as a one-line numeric block (`Taste markers (1-5 preference scale): Acidity 5/5, Tannin 3/5, ...`) directly under the prose taste profile so Claude can cite specific axes in its reasoning.
- `palate_persona`: `str | None` — 2-3 sentence sommelier persona from `synthesize_palate_from_notes()`. When present, quoted verbatim under a `**PALATE PERSONA**` header inserted *above* the `PRIORITY — Owner taste profile` block. Claude is instructed to cite these signals in `fits` tags.

**Outputs**: Complete system prompt string (1000+ words) with embedded JSON schema.

## Key Functions

**`format_bottle(b)`**: Return "{Vintage} {Producer} {Wine} (drink {Begin}–{End})". Skip empty fields.

**`build_system_prompt(...)`**:
  1. Use `taste_profile_override` if provided; otherwise call `build_enriched_profile_text_basic()`
  2. If `profile_source == "seed_bottles"`, prepend directional-profile caveat
  3. Format relevant bottles into bulleted list (max 20)
  4. Build `CONSTRAINTS` section: always includes bottle count; adds budget ceiling when set
  5. Embed sommelier persona: 70% profile weight, 30% meal weight (explicit in prompt)
  6. Add HARD CONSTRAINT: recommendations must come from the restaurant list only
  7. Inject `### TONIGHT'S MEAL` section if `meal_hints` provided
  8. Embed full JSON schema with field descriptions for all enrichment fields
  9. Append reasoning structure notes (4-step format), confidence format note, fits field note, wheel/bars/drink notes
  10. Return full prompt; also writes to `prompt.log` via dedicated `_prompt_logger`

## Profile Function Disambiguation

Two separate functions live in `profile.py`; `prompt.py` uses the first:

- **`build_enriched_profile_text_basic()`** — formats the frequency-derived taste profile as prose (no LLM call). Called by `build_system_prompt()` when no `taste_profile_override` is provided.
- **`build_enriched_profile_text(anthropic_api_key, anthropic_model)`** — calls Claude first to enrich the profile with multi-word style phrases, then formats. Called from `routes/recommend.py` before the main recommendation call; the result is passed in as `taste_profile_override`.

## Reasoning Field Structure (enforced in prompt)

The prompt instructs the LLM to follow a 4-step structure for `reasoning`:
1. **Personal comparison** (required): `"Like your [owned bottle], but [how it differs/excels]."` — only when a real cellar match exists; otherwise open by naming a concrete preference from the taste profile.
2. **Contrast** (where relevant): `"Unlike [avoided style/bottle], no [unwanted trait]."`
3. **Food context** (secondary): Meal synergy only if it adds genuine insight.
4. **Cellar note**: If outclassed by owned wine, or worth ordering despite similarity.

## Confidence Field Format (enforced in prompt)

`"[high|medium|low] — [single clause reason]"`
Examples: `"high — hits your preference for grower Champagne with mineral complexity"` / `"medium — right style but the vintage may be too young"`

## Fits Field (enforced in prompt)

Optional per-recommendation `fits: string[]` — 2–3 short tags (each ≤ 8 words) that ground the pick in a concrete signal from the taste profile. The prompt requires each tag to cite a real signal: a top region/varietal/producer, a preferred descriptor, an avoided style, a numeric taste marker (e.g. "Acidity 5/5"), or a phrase quoted/paraphrased from the `PALATE PERSONA` block. Generic phrases ("Great with food", "Crowd pleaser") are forbidden. The model is instructed to omit the field entirely (not return an empty array) when no clean signal applies.

## Wheel, Bars, Drink Notes (enforced in prompt)

- **`wheel`**: 6–8 entries using real aroma vocabulary (e.g., "Dried Cherry", "Tar", "Violets", "Cedar"). Values 0–10 intensity.
- **`bars`**: Values 0–10, calibrated to style (e.g., lean Chablis: tannin ≈ 1, acidity ≈ 9; big Amarone: tannin ≈ 9).
- **`drink`**: Integer years grounded in vintage. `from` = earliest to open; `peak` = optimal; `until` = last acceptable.

## Pattern & Gotchas

- **Sommelier persona**: "Be direct. No filler. Respond with ONLY valid JSON (no markdown, no backticks, no explanation)."
- **Priority weighting**: 70% profile / 30% meal is stated explicitly in the prompt to prevent meal overriding profile fit.
- **Prompt logging**: Every built prompt is written to `backend/prompt.log` via `_prompt_logger` (separate from the main sommelier logger, does not propagate). Useful for debugging prompt drift.
- **Schema in prompt**: Inline JSON schema in prompt.py is a reference copy for the LLM's benefit; the authoritative schema for validation is `_RECOMMENDATION_TOOL` in `recommender.py`.
- **Constraints section**: Both `bottle_count` and `budget_ceiling` are injected into a `CONSTRAINTS` block. The route passes these through from the form submission.
- **Cellar context**: Notes if recommendation is outclassed by home inventory or worth ordering despite owning similar wines.
- **Relevant bottles**: Up to 20 shown; helps LLM avoid recommending something user already owns.

## Testing

Verify prompt is sent to Claude with complete taste profile, cellar context, and constraints section. Check that `bottle_count` and `budget_ceiling` appear correctly in the CONSTRAINTS block.
