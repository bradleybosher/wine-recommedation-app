# recommender.py

## Responsibility

Call Anthropic Claude API with tool use for structured output, retry on schema validation failures, return validated recommendation or raise error.

## Dependencies

- `anthropic` (Anthropic Python SDK — manages HTTP, retries, auth)
- `json` (serialising tool input to llm.log)
- `pydantic.ValidationError` (schema validation errors)
- `models.RecommendationResponse` (output schema)

## Inputs/Outputs

**Inputs** (to `get_recommendation()`):
- `wine_list_text`: Parsed text from wine list (PDF/text)
- `meal`: Meal description string
- `system_prompt`: Complete prompt with profile + schema
- `anthropic_api_key`, `anthropic_model`: Anthropic API configuration
- `image_b64`: Optional base64-encoded JPEG image for multimodal input

**Outputs**: `RecommendationResponse` (validated Pydantic model) or `HTTPException(502)`.

## Key Logic

### Public entry point: `get_recommendation()`

1. **Prompt construction**: `text_payload` = wine list + meal. If image provided, wine list omitted (Claude reads it from the image).
2. **Retry loop**: Up to `_MAX_ATTEMPTS = 3` attempts on `ValueError` (schema validation failure). API errors abort immediately.
3. Each attempt calls `_attempt_recommendation()`.

### `_attempt_recommendation()`

<<<<<<< HEAD
1. Call `_call_ollama()` with `_RESPONSE_SCHEMA` (structured output).
<<<<<<< HEAD
2. If Ollama returns 400 or 500 (old version or overloaded, rejects schema dict): retry with `format="json"` (plain JSON mode).
=======
2. If Ollama returns 400 (old version, rejects schema dict): retry with `format="json"` (plain JSON mode).
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
3. Parse `message.content` (chat) or `response` (generate) from body.
4. Strip markdown fences if present.
5. Repair truncated JSON: count `{` vs `}`, append missing closing braces.
6. `json.loads()` — raise `ValueError` on failure.
7. Garbage key detection: if any key is `""` or contains `"<|"`, raise `ValueError`.
8. `RecommendationResponse(**data)` — raise `ValueError` on Pydantic schema mismatch.
=======
1. Build Anthropic `messages` content: optional image block (type=`"image"`, source=base64) + text block.
2. Call `client.messages.create()` with `tools=[_RECOMMENDATION_TOOL]` and `tool_choice={"type": "tool", "name": "provide_recommendations"}` — forces Claude to use the tool.
3. Extract the `tool_use` block from `response.content` by name.
4. Read `tool_block.input` — already a parsed dict, no JSON parsing needed.
5. `RecommendationResponse(**data)` — raise `ValueError` on Pydantic schema mismatch.
6. Log system prompt + user payload + tool input dict to `llm.log`.
>>>>>>> 90359d9 (Ported to Anthropic)

## Tool Definition (`_RECOMMENDATION_TOOL`)

Passed to Claude as a tool; `tool_choice` forces its use, giving structured output without JSON parsing.

Key schema fields:
- `recommendations[].reasoning`: 2–4 sentences opening with personal comparison to owned bottle.
- `recommendations[].confidence`: Format `"high|medium|low — single clause reason"`.
- `recommendations[].fit_markers`: Optional array of 2–3 short tags (each ≤ 8 words) grounding the pick in a concrete profile signal (top region/varietal/producer, preferred descriptor, avoided style, or taste-marker level). Claude is instructed to omit the field entirely (not return an empty array) when no clean signal applies.
- `profile_match_summary`: Required top-level field.
- `list_quality_note`: Optional top-level string.

## Patterns & Gotchas

<<<<<<< HEAD
- **Timeout**: 120-second timeout per attempt (Ollama can be slow on CPU). Total max wall time ≈ 6 minutes (3 × 120s).
- **Retry classification**: `ValueError` (bad output) → retry. `httpx.HTTPStatusError` or `Exception` (network/HTTP error) → raise 502 immediately, no retry.
- **Markdown fences**: Always stripped despite prompt instruction ("ONLY valid JSON").
- **Truncated JSON repair**: Counts `{`/`}` imbalance, appends missing `}`. Protects against cut-off responses.
- **Garbage keys**: `""` key or `"<|"` prefix (special-token leakage) → raise ValueError → trigger retry.
- **Dual response formats**: `body["message"]["content"]` (chat endpoint) OR `body["response"]` (generate endpoint). Both handled.
<<<<<<< HEAD
- **Schema fallback**: Ollama < 0.5.1 returns 400 for `format=<dict>` → falls back to `format="json"` automatically per attempt. Code also catches 500 in the same check.
- **Extended alias recovery for `wine_name`**: After fixed aliases (`name`, `wineName`, `title`), code also checks `wine`, `label`, `bottle`, `category`, `varietal`, `grape` in order; last resort picks the shortest string field in the item dict.
- **Extended alias recovery for `reasoning`**: After fixed aliases (`description`, `explanation`, `notes`), code also checks `rationale`, `match`, `why`, `comment`, `detail` in order; last resort picks the longest remaining string field, or synthesises from a numeric `score` field if present (`"Rated N/10 against the taste profile…"`).
- **`confidence` synthesis**: If missing entirely, derived from `score` field (≥9.0 → high, ≥7.5 → medium, else low); defaults to `"low"` if no score present.
=======
- **Schema fallback**: Ollama < 0.5.1 returns 400 for `format=<dict>` → falls back to `format="json"` automatically per attempt.
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
- **Tool use = no JSON repair**: `tool_block.input` is a pre-parsed dict. All brace-repair, fence-stripping, and key-aliasing logic from the prior Ollama implementation has been removed.
- **Retry classification**: `ValueError` (Pydantic validation failure) → retry up to 3×. `anthropic.APIError` or other exceptions → raise 502 immediately.
- **Multimodal**: Images passed as `{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": <b64>}}` content block. Must be JPEG; media type hardcoded.
- **Max tokens**: 4096 (sufficient for 3 recommendations with reasoning).
- **No timeout config**: Anthropic SDK uses its own default timeouts and built-in retry for transient errors.
>>>>>>> 90359d9 (Ported to Anthropic)

## Known Issues / TODOs

- Image media type hardcoded to `image/jpeg`; PNG uploads would need the media type inferred from the upload.
- LLM temperature not configurable (uses Anthropic defaults).
- No exponential backoff between retries (immediate retry).

## Testing

1. Upload wine list PDF + meal description → valid `RecommendationResponse` returned.
2. Upload wine list image (multimodal path) → same response structure.
3. Verify `llm.log` shows `--- TOOL USE INPUT (PARSED) ---` with a JSON dict.
4. Schema validation failure (e.g. missing `profile_match_summary`) → retries then raises HTTPException(502).
5. Invalid API key → immediate HTTPException(502), no retry.
