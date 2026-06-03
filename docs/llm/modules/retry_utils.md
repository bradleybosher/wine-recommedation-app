# retry_utils.py

## Responsibility

Shared retry helper for transient failures, primarily Anthropic API calls. Wraps a zero-argument callable with bounded retries and exponential backoff.

## Public surface

- `call_with_retry(fn, *, max_attempts: int = 3, retryable_on: tuple = (Exception,))` — Call `fn()` up to `max_attempts` times. Returns `fn()`'s value on the first success. Retries only on exceptions whose type is in `retryable_on`; any exception **not** in that tuple is re-raised immediately. If every attempt fails, the **last** exception is re-raised. Between attempts it sleeps `1.5 ** attempt` seconds (exponential backoff; attempt counts from 1). No sleep is taken after the final attempt.

## Constants

- `_DEFAULT_MAX_ATTEMPTS: int = 3`
- `_DEFAULT_BACKOFF_BASE: float = 1.5` — seconds; delay for a given retry is `base ** attempt`.

## Dependencies

- `logging`, `time` (standard library)
- `logger` — `logging.getLogger("sommelier.retry")`; logs a warning before each retry and an error when all attempts are exhausted.

## Patterns & Gotchas

- **Zero-arg callable**: `fn` must take no arguments. Bind parameters with `functools.partial` or a lambda before passing.
- **Selective retry**: pass a narrower `retryable_on` (e.g. specific Anthropic/transport exception types) to avoid retrying on programmer errors; the default `(Exception,)` retries on everything.
- **Last-exception semantics**: callers see the final failure, not the first, when all attempts are exhausted.
- **Backoff is exponential, not linear**: delays for default settings are ~1.5s then ~2.25s before the 2nd and 3rd attempts.

## Testing

1. `fn` succeeds on first call; assert it is invoked exactly once and its value returned.
2. `fn` raises a retryable exception twice then succeeds; assert it is called 3 times and the value returned.
3. `fn` always raises a retryable exception; assert it is called `max_attempts` times and the last exception propagates.
4. `fn` raises a non-retryable exception (not in `retryable_on`); assert it is called once and the exception propagates immediately.
