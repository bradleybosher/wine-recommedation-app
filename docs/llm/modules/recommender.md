# recommender.py

## Responsibility

Call Anthropic Claude API with tool use for structured output, derive wine palette server-side, retry on schema validation failures, return validated recommendation or raise error.

## Dependencies

- `anthropic` (Anthropic Python SDK — manages HTTP, retries, auth)
- `llm_client.call_claude` (telemetry wrapper around `client.messages.create`)
- `json` (serialising tool input to llm.log)
- `pydantic.ValidationError` (schema validation errors)
- `unicodedata` (NFKD normalisation for accent-insensitive reference matching)
- `models.RecommendationResponse`, `models.WineColor`, `models.WineRecommendation`, `models.StructureBars`
- `backend/data/wine_reference.json` — seed table of canonical bars per appellation/grape pair (loaded at module level)

## Inputs/Outputs

**Inputs** (to `get_recommendation()`):
- `wine_list_text`: Parsed text from wine list (PDF/text)
- `meal`: Meal description string
- `system_prompt`: Complete prompt with profile + schema
- `anthropic_api_key`, `anthropic_model`: Anthropic API configuration
- `image_b64`: Optional base64-encoded JPEG image for multimodal input
- `source_mode`: `str` (default `"winelist"`) — `"winelist"` builds the user prompt around the restaurant wine list; `"cellar"` builds a different prompt that recommends from the cellar inventory in the system prompt alone (no wine list text)

**Outputs**: `RecommendationResponse` (validated Pydantic model) or `HTTPException(502)`.

## Key Logic

### Public entry point: `get_recommendation(..., source_mode: str = "winelist")`

1. **Prompt construction** — branches on `source_mode`:
   - `"winelist"` (default): `user_prompt` instructs Claude to survey every wine on the restaurant list and rank the top 3, recommending ONLY wines on the list. `text_payload` = wine list text + the meal line + user prompt. If an image is provided, the wine list text is omitted (Claude reads it from the image).
   - `"cellar"`: `user_prompt` instructs Claude to survey every bottle in the **CELLAR INVENTORY** block of the system prompt, score each against the taste profile, and rank the top bottles — recommending ONLY bottles in the inventory (no hallucination). No wine list text is included; `text_payload` is just the user prompt + meal line.
2. **Retry loop**: Up to `_MAX_ATTEMPTS = 3` attempts on `ValueError` (schema validation failure). API errors abort immediately.
3. Each attempt calls `_attempt_recommendation()`.

### `_attempt_recommendation()`

0. **Replay shortcircuit**: If `RECORDED_RESPONSES_DIR` env var is set, load the first `.json` fixture alphabetically from that directory, validate it as `RecommendationResponse`, derive colors, and return immediately — no API call. Used for UI development without spending API budget.
1. Build Anthropic `messages` content: optional image block (type=`"image"`, source=base64) + text block.
2. Call `call_claude("recommend", client, ...)` (telemetry wrapper) with `tools=[_RECOMMENDATION_TOOL]` and `tool_choice={"type": "tool", "name": "provide_recommendations"}` — forces Claude to use the tool.
3. Extract the `tool_use` block from `response.content` by name.
4. Read `tool_block.input` — already a parsed dict, no JSON parsing needed.
5. `RecommendationResponse(**data)` — raise `ValueError` on Pydantic schema mismatch.
6. **Color derivation**: For each `WineRecommendation` where `color is None`, call `_derive_color(wine)` and assign.
7. **Bar blending**: For each wine with `bars` populated, call `_find_reference_bars(appellation, grape)`. When a match is found in `_WINE_REFERENCE`, blend Claude's bars 50/50 with the reference values via `_blend_bars()`. This grounds LLM-asserted bar values against a calibrated seed table.
8. Log system prompt + user payload + tool input dict to `llm.log`.

### `_derive_color(wine: WineRecommendation) → WineColor`

Keyword-match on `grape + region + wine_name` to select a palette. Mirrors the frontend's `derivePalette` logic so visual output is consistent even before full type sync.

Palettes (module-level constants — glass hex values mirror `frontend/src/design/tokens.ts`):
- `_PALETTE_BRUNELLO` — Sangiovese / Chianti / Brunello / Montalcino (`glass='#7d1f24'`)
- `_PALETTE_BAROLO` — Nebbiolo / Barolo / Barbaresco / Piedmont / Piemonte (`glass='#8a2a2e'`)
- `_PALETTE_CHABLIS` — Chardonnay / Chablis / Bourgogne Blanc; also generic whites (`glass='#b8932a'` — darkened for luminance contrast on cream paper)
- `_PALETTE_ROSE` — Rosé wines (`glass='#c44a6a'` — deepened for luminance separation from paper background)
- `_PALETTE_AMBER` — Orange/amber wines (`glass='#a86420'` — shifted hue for deuteranope legibility)
- `_PALETTE_DEFAULT` — everything else (same hex values as `_PALETTE_BRUNELLO`)

`color` is intentionally **excluded from the Claude tool schema** to avoid hallucinated hex codes.

## Tool Definition (`_RECOMMENDATION_TOOL`)

Passed to Claude as a tool; `tool_choice` forces its use, giving structured output without JSON parsing.

Key schema fields per recommendation item:
- `rank`, `wine_name`: required
- `reasoning`: 2–4 sentences, opening with personal comparison to owned bottle or named profile preference
- `confidence`: `"high|medium|low — single clause reason"`
- `fits`: Optional array of 2–3 short tags (≤ 8 words each) grounding the pick in a concrete profile signal. Omit entirely when no clean signal applies (no empty array).
- `evidence_quotes`: Optional array of 1–2 short verbatim quotes from the TASTING NOTE LIBRARY in the system prompt. Format: `'From your [Wine name] note: "[verbatim quote]"'`. Only populated when the library is present and a genuine textual match exists — never fabricated or paraphrased. Omitted entirely when no library or no clear match.
- `stretch`: Boolean. `true` only when this pick is intentionally outside the safe persona zone (the stretch/discovery slot, typically the final ranked pick). Omit or `false` for all other picks.
- `appellation`, `country`, `coords`, `grape`, `abv`: Optional enrichment
- `drink`: Optional object `{from, peak, until}` (integer years)
- `bars`: Optional object `{tannin, acidity, body, sweetness, oak}` (0–10 each) — **post-validation, these are blended 50/50 with reference values when a match exists in `_WINE_REFERENCE`**
- `wheel`: Optional object — 6–8 aroma descriptors with intensity 0–10
- `nose`, `palate`: Optional one-sentence strings
- `pairs`: Optional array of 2–4 food pairing suggestions
- `critic`: Optional object `{score, source}`
- `color` is **not** in the tool schema — derived server-side only

Top-level schema fields:
- `recommendations`: required array
- `profile_match_summary`: required string
- `list_quality_note`: optional string

## Bar Blending Helpers

### `_normalize_ref(s: str) → str`
Lowercase + strip combining diacritics (NFKD) for accent-insensitive reference matching. Same normalisation as `retrieval._normalize`.

### `_get_norm_reference() → list[tuple[str, str, dict]]`
Returns the reference table pre-normalized to `(norm_appellation, norm_grape, bars)` tuples so per-wine lookups don't re-run NFKD normalization across the whole table on every call. Cached in module state and rebuilt only when the source `_WINE_REFERENCE` list object changes identity (detected with `is`, which also keeps the prior object alive to avoid id reuse). In production it is computed once on first lookup; tests that monkeypatch `_WINE_REFERENCE` trigger a rebuild automatically.

### `_find_reference_bars(appellation, grape) → Optional[dict]`
Searches the pre-normalized table from `_get_norm_reference()` (sourced from `_WINE_REFERENCE`, loaded from `data/wine_reference.json` at module level) for the best match using three tiers:
1. Exact appellation + exact grape
2. Partial appellation (appellation substring in entry) + exact grape
3. Appellation-only (ignores grape)
Returns the bars dict (0.0–1.0 scale) of the first match, or `None`.

### `_blend_bars(claude_bars: dict, ref_bars: dict) → dict`
50/50 blend of Claude's 0–10 bars with reference 0.0–1.0 bars (scaled ×10 before averaging).
Keys: `tannin`, `acidity`, `body`, `sweetness`, `oak`. Values rounded to 1 decimal place.

**Scale note**: `wine_reference.json` stores values on 0.0–1.0 scale; blending ALWAYS multiplies reference values ×10 before the 50/50 average with Claude's 0–10 values.

## Patterns & Gotchas

- **Tool use = no JSON repair**: `tool_block.input` is a pre-parsed dict. All brace-repair, fence-stripping, and key-aliasing logic from the prior Ollama implementation has been removed.
- **Retry classification**: `ValueError` (Pydantic validation failure) → retry up to 3×. `anthropic.APIError` or other exceptions → raise 502 immediately.
- **Color always populated**: `_derive_color` runs post-validation, so `wine.color` is never `None` on any returned `WineRecommendation`.
- **Bar blending is optional**: only fires when `wine.bars` is not `None` AND a reference entry matches. No blending → Claude's bars used as-is.
- **Reference load failure**: if `data/wine_reference.json` is missing or malformed, `_WINE_REFERENCE` is set to `[]` (empty list) and blending silently skips for all wines.
- **Multimodal**: Images passed as `{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": <b64>}}` content block. Must be JPEG; media type hardcoded.
- **Max tokens**: 4096 (sufficient for 3 recommendations with full enrichment fields).
- **No timeout config**: Anthropic SDK uses its own default timeouts and built-in retry for transient errors.
- **Error response messages**: HTTP 502 responses contain generic user-safe messages only. Exception types and detailed error messages are logged internally but never exposed to clients.

## Known Issues / TODOs

- Image media type hardcoded to `image/jpeg`; PNG uploads would need the media type inferred from the upload.
- LLM temperature not configurable (uses Anthropic defaults).
- No exponential backoff between retries (immediate retry).

## Testing

1. Upload wine list PDF + meal description → valid `RecommendationResponse` returned with `color` populated on every wine.
2. Upload wine list image (multimodal path) → same response structure.
3. Verify `llm.log` shows `--- TOOL USE INPUT (PARSED) ---` with a JSON dict.
4. Schema validation failure (e.g. missing `profile_match_summary`) → retries then raises HTTPException(502).
5. Invalid API key → immediate HTTPException(502), no retry.
6. Verify `_derive_color` returns `_PALETTE_BAROLO` for a Nebbiolo, `_PALETTE_CHABLIS` for a Riesling, `_PALETTE_DEFAULT` for an unknown red.
