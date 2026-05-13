# rate_limit.py

## Responsibility

In-process IP-based rate limiter used by `/recommend`.

## Public surface

- `check_rate_limit(ip: str) -> None` — raises `HTTPException(status_code=429)` if `ip` has issued ≥ 10 requests in the last 60 s. Otherwise records the timestamp and returns.

## Constants

- `_RATE_LIMIT_MAX = 10`, `_RATE_LIMIT_WINDOW = 60`.

## Patterns & Gotchas

- State lives in module-level `_rate_counts: dict[str, list[float]]`. Process-local; resets on restart. Adequate for a portfolio app, not for multi-worker production.
- Only `/recommend` calls this; uploads are not rate-limited (size cap is the primary defence there).
