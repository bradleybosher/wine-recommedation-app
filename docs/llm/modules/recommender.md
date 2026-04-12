# recommender.py

## Responsibility

Call Ollama LLM with structured output schema, retry on garbage/invalid responses, parse and validate JSON, return structured recommendation or raise error.

## Dependencies

- `httpx` (sync HTTP client — not async despite FastAPI context; used inside `with httpx.Client()`)
- `json`, `re` (JSON parsing + markdown fence stripping)
- `pydantic.ValidationError` (schema validation errors)
- `models.RecommendationResponse` (output schema)

## Inputs/Outputs

**Inputs** (to `get_recommendation()`):
- `wine_list_text`: Parsed text from wine list (PDF/text)
- `meal`: Meal description string
- `system_prompt`: Complete prompt with profile + schema
- `ollama_url`, `ollama_model`: Ollama configuration
- `image_b64`: Optional base64-encoded image for vision models

**Outputs**: `RecommendationResponse` (validated Pydantic model) or `HTTPException(502)`.

## Key Logic

### Public entry point: `get_recommendation()`

1. **Prompt construction**: `text_payload` = wine list + meal. If image provided, wine list omitted (vision model reads it directly).
2. **Retry loop**: Up to `_MAX_ATTEMPTS = 3` attempts on `ValueError` (bad LLM output). Network/HTTP errors abort immediately.
3. Each attempt calls `_attempt_recommendation()`.

### `_attempt_recommendation()`

1. Call `_call_ollama()` with `_RESPONSE_SCHEMA` (structured output).
2. If Ollama returns 400 (old version, rejects schema dict): retry with `format="json"` (plain JSON mode).
3. Parse `message.content` (chat) or `response` (generate) from body.
4. Strip markdown fences if present.
5. Repair truncated JSON: count `{` vs `}`, append missing closing braces.
6. `json.loads()` — raise `ValueError` on failure.
7. Garbage key detection: if any key is `""` or contains `"<|"`, raise `ValueError`.
8. `RecommendationResponse(**data)` — raise `ValueError` on Pydantic schema mismatch.

### `_call_ollama()`

- POST to `/api/chat` with system+user messages and `format=<schema>`.
- If 404: fall back to `/api/generate` with same schema.

## Structured Output Schema (`_RESPONSE_SCHEMA`)

Grammar-constrained sampling — forces Ollama to emit exact keys/types. Requires Ollama ≥ 0.5.1. Falls back to `format="json"` on 400.

Key schema fields:
- `recommendations[].reasoning`: Requires 2–4 sentences opening with a personal comparison to owned bottle.
- `recommendations[].confidence`: Format `"high|medium|low — single clause reason"`.
- `profile_match_summary`: Required top-level field.
- `list_quality_note`: Optional top-level string.

## Patterns & Gotchas

- **Timeout**: 120-second timeout per attempt (Ollama can be slow on CPU). Total max wall time ≈ 6 minutes (3 × 120s).
- **Retry classification**: `ValueError` (bad output) → retry. `httpx.HTTPStatusError` or `Exception` (network/HTTP error) → raise 502 immediately, no retry.
- **Markdown fences**: Always stripped despite prompt instruction ("ONLY valid JSON").
- **Truncated JSON repair**: Counts `{`/`}` imbalance, appends missing `}`. Protects against cut-off responses.
- **Garbage keys**: `""` key or `"<|"` prefix (special-token leakage) → raise ValueError → trigger retry.
- **Dual response formats**: `body["message"]["content"]` (chat endpoint) OR `body["response"]` (generate endpoint). Both handled.
- **Schema fallback**: Ollama < 0.5.1 returns 400 for `format=<dict>` → falls back to `format="json"` automatically per attempt.

## Known Issues / TODOs

- Image support tested at integration level; assumes Ollama vision model supports `messages[i]["images"]` field.
- Timeout hardcoded at 120s (not configurable via env).
- LLM temperature/seed not configurable (uses Ollama defaults).
- No exponential backoff between retries (immediate retry).

## Testing

Test with a wine list PDF + meal description + valid Ollama endpoint. Verify:
1. JSON with markdown fences (` ```json ... ``` `) is parsed correctly.
2. Truncated JSON (missing `}`) is repaired and parsed.
3. Invalid JSON exhausts retries and raises HTTPException(502).
4. Valid JSON with missing required fields raises HTTPException(502).
5. Valid complete JSON returns RecommendationResponse.
6. Old Ollama (400 on schema dict) falls back to plain JSON mode and succeeds.
