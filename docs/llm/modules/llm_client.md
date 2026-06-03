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
    retryable_on: tuple = (anthropic.APIConnectionError, anthropic.RateLimitError),
    max_attempts: int = 3,
    **kwargs,
) -> anthropic.types.Message
```

Retries on transient API errors **by default** — `retryable_on` defaults to `(anthropic.APIConnectionError, anthropic.RateLimitError)`, so every call site gets connection/rate-limit retries unless it overrides the tuple.

Calls `client.messages.create(**kwargs)` and logs one JSON line to `backend/logs/llm_calls.jsonl` per call containing:

| Field | Description |
|---|---|
| `ts` | Unix epoch timestamp (`time.time()`, float seconds) |
| `purpose` | Caller-supplied label (see `Purpose` type) |
| `model` | Model ID from `kwargs["model"]` |
| `in_tokens` | `usage.input_tokens` from response |
| `out_tokens` | `usage.output_tokens` from response |
| `ms` | Wall-clock latency in milliseconds |
| `cost_usd` | Estimated cost (pricing table in `MODEL_PRICING`) |

## Retry Logic

Retries are **on by default**: `retryable_on` defaults to `(anthropic.APIConnectionError, anthropic.RateLimitError)`, so connection resets and rate-limit errors are retried for every caller unless it passes a different tuple (e.g. `()` to disable). When a raised exception matches `retryable_on`, the call is retried up to `max_attempts - 1` times (via `retry_utils.call_with_retry`) with a 1 s, 2 s back-off. Non-retryable exceptions propagate immediately.

## Cost Estimation

Module-level `MODEL_PRICING` dict maps model IDs to `(input_usd, output_usd)` per million tokens; `_DEFAULT_PRICING` `(3.00, 15.00)` is the conservative fallback for unknown models. Costs are estimates; actual billing may differ.

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
