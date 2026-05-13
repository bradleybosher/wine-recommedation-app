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

- **Tool use = no JSON repair**: `tool_block.input` is a pre-parsed dict. All brace-repair, fence-stripping, and key-aliasing logic from the prior Ollama implementation has been removed.
- **Retry classification**: `ValueError` (Pydantic validation failure) → retry up to 3×. `anthropic.APIError` or other exceptions → raise 502 immediately.
- **Multimodal**: Images passed as `{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": <b64>}}` content block. Must be JPEG; media type hardcoded.
- **Max tokens**: 4096 (sufficient for 3 recommendations with reasoning).
- **No timeout config**: Anthropic SDK uses its own default timeouts and built-in retry for transient errors.
- **Error response messages**: HTTP 502 responses contain generic user-safe messages only (e.g., "Recommendation provider experienced an API error. Please try again." or "Recommendation provider failed. Please try again."). Exception types and detailed error messages are logged internally but never exposed to clients.

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
