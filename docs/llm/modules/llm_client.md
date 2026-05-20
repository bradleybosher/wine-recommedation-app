# llm_client.py

## Responsibility

Thin telemetry wrapper around the Anthropic SDK. Every Claude API call in the backend goes through `call_claude()`, which logs cost, latency, and token counts to a structured JSONL file for portfolio-visible observability.

## Dependencies

- `anthropic` (Anthropic Python SDK)
- `time`, `json`, `logging`, `pathlib`

## Public Interface

```python
Purpose = Literal["recommend", "enrich_profile", "seed_profile", "vision_parse", "synthesize_palate"]

def call_claude(
    purpose: Purpose,
    client: anthropic.Anthropic,
    *,
    retryable_on: tuple[type[Exception], ...] = (),
    max_attempts: int = 3,
    **kwargs,
) -> anthropic.types.Message
```

Calls `client.messages.create(**kwargs)` and logs one JSON line to `backend/logs/llm_calls.jsonl` per call containing:

| Field | Description |
|---|---|
| `ts` | ISO-8601 UTC timestamp |
| `purpose` | Caller-supplied label (see `Purpose` type) |
| `model` | Model ID from `kwargs["model"]` |
| `in_tokens` | `usage.input_tokens` from response |
| `out_tokens` | `usage.output_tokens` from response |
| `ms` | Wall-clock latency in milliseconds |
| `cost_usd` | Estimated cost (pricing table in `_COST_PER_MTok`) |

## Retry Logic

When `retryable_on` is provided and an exception matches, retries up to `max_attempts - 1` times with a 1 s, 2 s back-off. Non-retryable exceptions propagate immediately.

## Cost Estimation

Module-level `_COST_PER_MTok` dict maps model-ID prefixes to `(input_usd, output_usd)` per million tokens. Unknown models use a conservative fallback. Costs are estimates; actual billing may differ.

## Call Sites

| Purpose | Caller |
|---|---|
| `"recommend"` | `recommender._attempt_recommendation()` |
| `"enrich_profile"` | `profile.build_enriched_profile_text()` |
| `"seed_profile"` | `seed_profile.infer_profile_from_bottles()` |
| `"vision_parse"` | `parser._call_haiku_vision()` |
| `"synthesize_palate"` | `profile.synthesize_palate_from_notes()` |

## Debug Endpoint

`GET /debug/stats` (in `routes/debug.py`) reads `llm_calls.jsonl` and returns aggregate stats (total calls, total cost, avg latency) grouped by purpose. Protected by the same JWT auth as all other endpoints.

## Patterns & Gotchas

- **Import cost**: The log file is opened fresh on every call — no persistent file handle. Safe for multi-process use.
- **No PII**: `kwargs` are not logged (prompts may contain user data). Only numeric telemetry is written.
- **Rotation**: Log file is not rotated automatically. In production, use an external log shipper or cron-based rotation.
